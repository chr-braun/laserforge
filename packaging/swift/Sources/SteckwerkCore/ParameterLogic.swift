import Foundation

public struct ParameterSection: Identifiable, Sendable {
    public let id: String
    public let title: String?
    public let params: [Param]
}

/// Formularlogik ohne Oberfläche: Vorgaben, Sichtbarkeit, Abschnitte und Eingabeprüfung wie in der Weboberfläche.
public enum ParameterLogic {
    public static func defaults(for params: [Param]) -> [String: JSONValue] {
        var values: [String: JSONValue] = [:]
        for p in params {
            values[p.key] = p.defaultValue
        }
        return values
    }

    /// Wie `shown()` in web/index.html: jede Bedingung in `when` muss einen der erlaubten Werte treffen.
    public static func isVisible(_ param: Param, values: [String: JSONValue]) -> Bool {
        for (key, allowed) in param.when {
            let current = values[key] ?? .null
            if !allowed.contains(where: { $0.looselyEquals(current) }) {
                return false
            }
        }
        return true
    }

    /// Abschnitte in der Reihenfolge ihres ersten Auftretens; Parameter ohne Abschnitt kommen in einen Abschnitt ohne Titel.
    public static func sections(_ params: [Param]) -> [ParameterSection] {
        var order: [String] = []
        var grouped: [String: [Param]] = [:]
        for p in params {
            let key = p.section ?? ""
            if grouped[key] == nil { order.append(key) }
            grouped[key, default: []].append(p)
        }
        return order.map { key in
            ParameterSection(id: key.isEmpty ? "_" : key, title: key.isEmpty ? nil : key, params: grouped[key] ?? [])
        }
    }

    public static func clamp(_ value: Double, for param: Param) -> Double {
        var v = value
        if let min = param.min { v = Swift.max(v, min) }
        if let max = param.max { v = Swift.min(v, max) }
        return v
    }

    /// Bringt einen Wert in die Form, die die Engine für den Parameter erwartet.
    public static func coerce(_ value: JSONValue, for param: Param) -> JSONValue {
        switch param.kind {
        case .number:
            guard let d = value.doubleValue ?? value.stringValue.flatMap(parseNumber) else { return param.defaultValue }
            return .double(clamp(d, for: param))
        case .int:
            guard let d = value.doubleValue ?? value.stringValue.flatMap(parseNumber) else { return param.defaultValue }
            return .int(Int(clamp(d.rounded(), for: param)))
        case .bool:
            return .bool(value.boolValue ?? (param.defaultValue.boolValue ?? false))
        case .select:
            if param.options.contains(where: { $0.value.looselyEquals(value) }) { return value }
            return param.defaultValue
        case .text:
            var s = value.stringValue ?? value.displayText
            if let limit = param.maxlength, s.count > limit { s = String(s.prefix(limit)) }
            return .string(s)
        case .motiv:
            return value.stringValue.map(JSONValue.string) ?? param.defaultValue
        case .motive:
            guard let list = value.arrayValue else { return param.defaultValue }
            let limit = param.max.map { Int($0) } ?? list.count
            return .array(Array(list.prefix(limit)))
        case .unknown:
            return value
        }
    }

    /// Werte für eine Anfrage: nur bekannte Schlüssel, jeweils geprüft; Fehlendes kommt aus den Vorgaben.
    public static func requestValues(_ params: [Param], values: [String: JSONValue]) -> [String: JSONValue] {
        var out: [String: JSONValue] = [:]
        for p in params {
            out[p.key] = coerce(values[p.key] ?? p.defaultValue, for: p)
        }
        return out
    }

    /// Übernimmt Werte (z. B. vom Assistenten) und liefert die Schlüssel, die sich tatsächlich geändert haben.
    public static func apply(_ updates: [String: JSONValue], to values: inout [String: JSONValue], params: [Param]) -> [String] {
        var changed: [String] = []
        for p in params {
            guard let new = updates[p.key] else { continue }
            let coerced = coerce(new, for: p)
            if !(values[p.key] ?? p.defaultValue).looselyEquals(coerced) {
                values[p.key] = coerced
                changed.append(p.key)
            }
        }
        return changed
    }

    public static func parseNumber(_ text: String) -> Double? {
        Double(text.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: ",", with: "."))
    }

    /// Anzahl Nachkommastellen passend zur Schrittweite (0.05 → 2, 1 → 0).
    public static func decimals(for param: Param) -> Int {
        guard let step = param.step, step > 0 else { return param.kind == .number ? 1 : 0 }
        if step >= 1 && step.rounded() == step { return 0 }
        var digits = 0
        var s = step
        while s.rounded() != s && digits < 4 {
            s *= 10
            digits += 1
        }
        return digits
    }
}

/// Ein Eintrag eines Motiv-Listenparameters (Typ `motive`).
public struct MotivPlacement: Hashable, Sendable {
    public var motivID: String
    public var x: Double
    public var y: Double
    public var groesse: Double
    public var drehung: Double
    public var spiegeln: Bool
    public var art: String
    private var extra: [String: JSONValue]

    public init(json: JSONValue, fallbackArt: String = "schnitt") {
        let o = json.objectValue ?? [:]
        motivID = o["id"]?.stringValue ?? ""
        x = o["x"]?.doubleValue ?? 0
        y = o["y"]?.doubleValue ?? 0
        groesse = o["groesse"]?.doubleValue ?? 40
        drehung = o["drehung"]?.doubleValue ?? 0
        spiegeln = o["spiegeln"]?.boolValue ?? false
        art = o["art"]?.stringValue ?? fallbackArt
        extra = o.filter { !["id", "x", "y", "groesse", "drehung", "spiegeln", "art"].contains($0.key) }
    }

    public var json: JSONValue {
        var o = extra
        o["id"] = .string(motivID)
        o["x"] = .double(x)
        o["y"] = .double(y)
        o["groesse"] = .double(groesse)
        o["drehung"] = .double(drehung)
        o["spiegeln"] = .bool(spiegeln)
        o["art"] = .string(art)
        return .object(o)
    }

    public static func list(_ value: JSONValue?) -> [MotivPlacement] {
        (value?.arrayValue ?? []).map { MotivPlacement(json: $0) }
    }

    public static func json(_ list: [MotivPlacement]) -> JSONValue {
        .array(list.map(\.json))
    }
}
