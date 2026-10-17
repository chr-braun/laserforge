import Foundation
#if canImport(FoundationXML)
import FoundationXML
#endif

public enum LineKind: Sendable, Hashable {
    case cut
    case engrave
}

public struct Polyline: Sendable, Hashable {
    public let kind: LineKind
    public let points: [Point]
    public let closed: Bool
}

/// Geometrie eines Blattplans, gelesen aus dem SVG, das die Engine erzeugt (Pfade aus M/L/Z in mm).
public struct SheetGeometry: Sendable {
    public let width: Double
    public let height: Double
    public let lines: [Polyline]

    public var cutCount: Int { lines.filter { $0.kind == .cut }.count }
    public var engraveCount: Int { lines.filter { $0.kind == .engrave }.count }

    /// - Parameter engraveColor: Strichfarbe der Gravur aus den Material-Einstellungen (Standard #0000FF).
    public static func parse(svg: String, engraveColor: String = "#0000FF") -> SheetGeometry {
        let delegate = SVGDelegate(engraveColor: engraveColor.lowercased())
        let parser = XMLParser(data: Data(svg.utf8))
        parser.delegate = delegate
        _ = parser.parse()
        return SheetGeometry(width: delegate.width, height: delegate.height, lines: delegate.lines)
    }

    /// Zerlegt ein SVG-Pfadattribut in Teilpfade. Unterstützt M, L, H, V, Z (groß und klein).
    public static func subpaths(_ d: String) -> [(points: [Point], closed: Bool)] {
        var result: [(points: [Point], closed: Bool)] = []
        var current: [Point] = []
        var closed = false
        var command: Character = "M"
        var cursor = Point(x: 0, y: 0)
        var start = cursor
        var scanner = PathScanner(d)

        func finish() {
            if current.count >= 2 { result.append((current, closed)) }
            current = []
            closed = false
        }

        while let token = scanner.next() {
            switch token {
            case .command(let c):
                command = c
                if c == "Z" || c == "z" {
                    if !current.isEmpty {
                        closed = true
                        cursor = start
                        finish()
                    }
                }
            case .number(let first):
                switch command {
                case "M", "m":
                    guard let second = scanner.nextNumber() else { return result }
                    finish()
                    cursor = command == "M" ? Point(x: first, y: second) : Point(x: cursor.x + first, y: cursor.y + second)
                    start = cursor
                    current = [cursor]
                    command = command == "M" ? "L" : "l"
                case "L", "l":
                    guard let second = scanner.nextNumber() else { return result }
                    cursor = command == "L" ? Point(x: first, y: second) : Point(x: cursor.x + first, y: cursor.y + second)
                    if current.isEmpty { current = [start] }
                    current.append(cursor)
                case "H", "h":
                    cursor = Point(x: command == "H" ? first : cursor.x + first, y: cursor.y)
                    if current.isEmpty { current = [start] }
                    current.append(cursor)
                case "V", "v":
                    cursor = Point(x: cursor.x, y: command == "V" ? first : cursor.y + first)
                    if current.isEmpty { current = [start] }
                    current.append(cursor)
                default:
                    break
                }
            }
        }
        finish()
        return result
    }
}

private final class SVGDelegate: NSObject, XMLParserDelegate {
    let engraveColor: String
    var width: Double = 0
    var height: Double = 0
    var lines: [Polyline] = []
    private var stack: [(stroke: String?, layer: LineKind?)] = []

    init(engraveColor: String) {
        self.engraveColor = engraveColor
    }

    func parser(_ parser: XMLParser, didStartElement elementName: String, namespaceURI: String?,
                qualifiedName qName: String?, attributes: [String: String] = [:]) {
        let name = elementName.split(separator: ":").last.map(String.init) ?? elementName
        var layer: LineKind?
        if let id = attributes["id"], id.hasPrefix("layer-") {
            layer = id.lowercased().contains("gravur") ? .engrave : .cut
        }
        let parent = stack.last
        stack.append((attributes["stroke"] ?? parent?.stroke, layer ?? parent?.layer))

        if name == "svg" {
            readSize(attributes)
        } else if name == "path", let d = attributes["d"] {
            let kind = classify(stack.last!)
            for sub in SheetGeometry.subpaths(d) {
                lines.append(Polyline(kind: kind, points: sub.points, closed: sub.closed))
            }
        }
    }

    func parser(_ parser: XMLParser, didEndElement elementName: String, namespaceURI: String?,
                qualifiedName qName: String?) {
        if !stack.isEmpty { stack.removeLast() }
    }

    private func classify(_ state: (stroke: String?, layer: LineKind?)) -> LineKind {
        if let layer = state.layer { return layer }
        return state.stroke?.lowercased() == engraveColor ? .engrave : .cut
    }

    private func readSize(_ attributes: [String: String]) {
        if let box = attributes["viewBox"] {
            let values = box.split(whereSeparator: { $0 == " " || $0 == "," }).compactMap { Double($0) }
            if values.count == 4 {
                width = values[2]
                height = values[3]
                return
            }
        }
        width = Self.millimetres(attributes["width"]) ?? 0
        height = Self.millimetres(attributes["height"]) ?? 0
    }

    private static func millimetres(_ value: String?) -> Double? {
        guard let value else { return nil }
        return Double(value.trimmingCharacters(in: CharacterSet(charactersIn: "0123456789.-").inverted))
    }
}

private struct PathScanner {
    enum Token {
        case command(Character)
        case number(Double)
    }

    private let chars: [Character]
    private var index = 0

    init(_ text: String) {
        chars = Array(text)
    }

    mutating func next() -> Token? {
        skipSeparators()
        guard index < chars.count else { return nil }
        let c = chars[index]
        if c.isLetter && c != "e" && c != "E" {
            index += 1
            return .command(c)
        }
        if let n = readNumber() { return .number(n) }
        index += 1
        return next()
    }

    mutating func nextNumber() -> Double? {
        skipSeparators()
        return readNumber()
    }

    private mutating func skipSeparators() {
        while index < chars.count, chars[index] == " " || chars[index] == "," || chars[index].isNewline || chars[index] == "\t" {
            index += 1
        }
    }

    private mutating func readNumber() -> Double? {
        let begin = index
        var end = index
        if end < chars.count, chars[end] == "-" || chars[end] == "+" { end += 1 }
        var seenDot = false
        var digits = 0
        while end < chars.count {
            let c = chars[end]
            if c.isASCII && c.isNumber {
                digits += 1
            } else if c == "." && !seenDot {
                seenDot = true
            } else {
                break
            }
            end += 1
        }
        if digits > 0, end < chars.count, chars[end] == "e" || chars[end] == "E" {
            var e = end + 1
            if e < chars.count, chars[e] == "-" || chars[e] == "+" { e += 1 }
            let expStart = e
            while e < chars.count, chars[e].isASCII && chars[e].isNumber { e += 1 }
            if e > expStart { end = e }
        }
        guard digits > 0, let value = Double(String(chars[begin..<end])) else { return nil }
        index = end
        return value
    }
}
