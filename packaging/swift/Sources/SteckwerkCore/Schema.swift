import Foundation

/// Antwort von GET /api/schema.
public struct Schema: Decodable, Sendable {
    public let models: [String: ModelInfo]
    public let groups: [String]
    public let groupLabels: [String: String]
    public let config: [Param]
    public let motive: [Motiv]
    public let pakete: [PaketInfo]
    public let version: String?
    public let assistent: KISettings?

    enum CodingKeys: String, CodingKey {
        case models, groups, config, motive, pakete, version, assistent
        case groupLabels = "group_labels"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        models = try c.decode([String: ModelInfo].self, forKey: .models)
        groups = try c.decodeIfPresent([String].self, forKey: .groups) ?? []
        groupLabels = try c.decodeIfPresent([String: String].self, forKey: .groupLabels) ?? [:]
        config = try c.decodeIfPresent([Param].self, forKey: .config) ?? []
        motive = try c.decodeIfPresent([Motiv].self, forKey: .motive) ?? []
        pakete = try c.decodeIfPresent([PaketInfo].self, forKey: .pakete) ?? []
        version = try c.decodeIfPresent(String.self, forKey: .version)
        assistent = try? c.decodeIfPresent(KISettings.self, forKey: .assistent)
    }

    /// Modelle für die Seitenleiste: Gruppen in der Reihenfolge der Engine, darin nach Name sortiert.
    public var sidebarGroups: [ModelGroup] {
        var byGroup: [String: [ModelEntry]] = [:]
        for (id, info) in models {
            byGroup[info.group, default: []].append(ModelEntry(id: id, info: info))
        }
        let known = groups.filter { byGroup[$0] != nil }
        let extra = byGroup.keys.filter { !groups.contains($0) }.sorted()
        return (known + extra).map { g in
            let entries = (byGroup[g] ?? []).sorted {
                ($0.info.label.lowercased(), $0.id) < ($1.info.label.lowercased(), $1.id)
            }
            return ModelGroup(id: g, label: groupLabels[g] ?? g, models: entries)
        }
    }

    public func motiv(id: String) -> Motiv? {
        motive.first { $0.id == id }
    }
}

public struct ModelGroup: Identifiable, Hashable, Sendable {
    public let id: String
    public let label: String
    public let models: [ModelEntry]
}

public struct ModelEntry: Identifiable, Hashable, Sendable {
    public let id: String
    public let info: ModelInfo
}

public struct ModelInfo: Decodable, Hashable, Sendable {
    public let label: String
    public let group: String
    public let desc: String
    public let params: [Param]

    enum CodingKeys: String, CodingKey { case label, group, desc, params }

    public init(label: String, group: String, desc: String, params: [Param]) {
        self.label = label
        self.group = group
        self.desc = desc
        self.params = params
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        label = try c.decode(String.self, forKey: .label)
        group = try c.decodeIfPresent(String.self, forKey: .group) ?? ""
        desc = try c.decodeIfPresent(String.self, forKey: .desc) ?? ""
        params = try c.decodeIfPresent([Param].self, forKey: .params) ?? []
    }
}

public enum ParamKind: String, Sendable {
    case number, int, bool, select, text, motiv, motive, unknown

    init(engineType: String) {
        switch engineType {
        case "number", "num": self = .number
        case "int": self = .int
        case "bool", "flag": self = .bool
        case "select": self = .select
        case "text": self = .text
        case "motiv": self = .motiv
        case "motive": self = .motive
        default: self = .unknown
        }
    }
}

public struct ParamOption: Decodable, Hashable, Sendable {
    public let value: JSONValue
    public let label: String

    public init(value: JSONValue, label: String) {
        self.value = value
        self.label = label
    }

    enum CodingKeys: String, CodingKey { case value, label }

    public init(from decoder: Decoder) throws {
        if let c = try? decoder.container(keyedBy: CodingKeys.self) {
            value = try c.decode(JSONValue.self, forKey: .value)
            label = try c.decodeIfPresent(String.self, forKey: .label) ?? value.displayText
        } else {
            value = try decoder.singleValueContainer().decode(JSONValue.self)
            label = value.displayText
        }
    }
}

public struct Param: Decodable, Hashable, Sendable, Identifiable {
    public var id: String { key }
    public let key: String
    public let label: String
    public let type: String
    public let defaultValue: JSONValue
    public let options: [ParamOption]
    public let min: Double?
    public let max: Double?
    public let step: Double?
    public let unit: String
    public let help: String
    public let section: String?
    public let maxlength: Int?
    public let when: [String: [JSONValue]]
    public let arten: [ParamOption]

    public var kind: ParamKind { ParamKind(engineType: type) }

    enum CodingKeys: String, CodingKey {
        case key, label, type, options, min, max, step, unit, help, section, maxlength, when, arten
        case defaultValue = "default"
    }

    public init(key: String, label: String, type: String, defaultValue: JSONValue,
                options: [ParamOption] = [], min: Double? = nil, max: Double? = nil, step: Double? = nil,
                unit: String = "", help: String = "", section: String? = nil, maxlength: Int? = nil,
                when: [String: [JSONValue]] = [:], arten: [ParamOption] = []) {
        self.key = key
        self.label = label
        self.type = type
        self.defaultValue = defaultValue
        self.options = options
        self.min = min
        self.max = max
        self.step = step
        self.unit = unit
        self.help = help
        self.section = section
        self.maxlength = maxlength
        self.when = when
        self.arten = arten
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        key = try c.decode(String.self, forKey: .key)
        label = try c.decodeIfPresent(String.self, forKey: .label) ?? key
        type = try c.decodeIfPresent(String.self, forKey: .type) ?? "text"
        defaultValue = try c.decodeIfPresent(JSONValue.self, forKey: .defaultValue) ?? .null
        options = try c.decodeIfPresent([ParamOption].self, forKey: .options) ?? []
        min = try c.decodeIfPresent(Double.self, forKey: .min)
        max = try c.decodeIfPresent(Double.self, forKey: .max)
        step = try c.decodeIfPresent(Double.self, forKey: .step)
        unit = try c.decodeIfPresent(String.self, forKey: .unit) ?? ""
        help = try c.decodeIfPresent(String.self, forKey: .help) ?? ""
        section = try c.decodeIfPresent(String.self, forKey: .section)
        maxlength = try c.decodeIfPresent(Int.self, forKey: .maxlength)
        when = (try? c.decodeIfPresent([String: [JSONValue]].self, forKey: .when)) ?? [:]
        arten = try c.decodeIfPresent([ParamOption].self, forKey: .arten) ?? []
    }
}

/// Ein Motiv aus der Bibliothek; Koordinaten normiert (etwa -0.5…0.5).
public struct Motiv: Decodable, Hashable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let quelle: String
    public let eingebaut: Bool
    public let flaechen: [Flaeche]
    public let linien: [[Point]]

    enum CodingKeys: String, CodingKey { case id, name, quelle, eingebaut, flaechen, linien }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        quelle = try c.decodeIfPresent(String.self, forKey: .quelle) ?? ""
        eingebaut = try c.decodeIfPresent(Bool.self, forKey: .eingebaut) ?? false
        flaechen = (try? c.decodeIfPresent([Flaeche].self, forKey: .flaechen)) ?? []
        let raw = (try? c.decodeIfPresent([[[Double]]].self, forKey: .linien)) ?? []
        linien = raw.map(Point.list)
    }
}

public struct Flaeche: Decodable, Hashable, Sendable {
    public let aussen: [Point]
    public let loecher: [[Point]]

    enum CodingKeys: String, CodingKey { case aussen, loecher }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        aussen = Point.list(try c.decodeIfPresent([[Double]].self, forKey: .aussen) ?? [])
        loecher = (try c.decodeIfPresent([[[Double]]].self, forKey: .loecher) ?? []).map(Point.list)
    }
}

public struct Point: Hashable, Sendable {
    public var x: Double
    public var y: Double

    public init(x: Double, y: Double) {
        self.x = x
        self.y = y
    }

    static func list(_ raw: [[Double]]) -> [Point] {
        raw.compactMap { $0.count >= 2 ? Point(x: $0[0], y: $0[1]) : nil }
    }
}

/// Ein installiertes Themenpaket.
public struct PaketInfo: Decodable, Hashable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let version: String
    public let autor: String
    public let modelle: [String]
    public let fehler: String?

    enum CodingKeys: String, CodingKey { case id, name, version, autor, modelle, fehler }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        autor = try c.decodeIfPresent(String.self, forKey: .autor) ?? ""
        modelle = try c.decodeIfPresent([String].self, forKey: .modelle) ?? []
        fehler = try? c.decodeIfPresent(String.self, forKey: .fehler)
    }
}

/// Assistent- und Bild-Einstellungen aus dem Schema (Schlüssel selbst liefert die Engine nie).
public struct KISettings: Decodable, Sendable {
    public let an: Bool
    public let url: String
    public let modell: String
    public let bilder: BildSettings?

    enum CodingKeys: String, CodingKey { case an, url, modell, bilder }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        an = (try? c.decodeIfPresent(Bool.self, forKey: .an)) ?? false
        url = (try? c.decodeIfPresent(String.self, forKey: .url)) ?? ""
        modell = (try? c.decodeIfPresent(String.self, forKey: .modell)) ?? ""
        bilder = try? c.decodeIfPresent(BildSettings.self, forKey: .bilder)
    }
}

public struct BildSettings: Decodable, Sendable {
    public let quelle: String
    public let ollamaModell: String
    public let openrouterModell: String
    public let chatgptModell: String
    public let keyGesetzt: Bool
    /// Ob je Anbieter ein Schlüssel hinterlegt ist (z. B. ["openrouter": true]); nie der Schlüssel selbst.
    public let keys: [String: Bool]
    public let limit: Double
    public let stile: [ParamOption]

    enum CodingKeys: String, CodingKey {
        case quelle, limit, stile, keys
        case ollamaModell = "ollama_modell"
        case openrouterModell = "openrouter_modell"
        case chatgptModell = "chatgpt_modell"
        case keyGesetzt = "key_gesetzt"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        quelle = (try? c.decodeIfPresent(String.self, forKey: .quelle)) ?? "ollama"
        ollamaModell = (try? c.decodeIfPresent(String.self, forKey: .ollamaModell)) ?? ""
        openrouterModell = (try? c.decodeIfPresent(String.self, forKey: .openrouterModell)) ?? ""
        chatgptModell = (try? c.decodeIfPresent(String.self, forKey: .chatgptModell)) ?? ""
        keyGesetzt = (try? c.decodeIfPresent(Bool.self, forKey: .keyGesetzt)) ?? false
        keys = (try? c.decodeIfPresent([String: Bool].self, forKey: .keys)) ?? [:]
        limit = (try? c.decodeIfPresent(Double.self, forKey: .limit)) ?? 0
        stile = (try? c.decodeIfPresent([ParamOption].self, forKey: .stile)) ?? []
    }
}
