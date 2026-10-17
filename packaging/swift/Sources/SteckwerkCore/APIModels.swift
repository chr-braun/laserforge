import Foundation

public struct PingResponse: Decodable, Sendable {
    public let ok: Bool
    public let app: String?
    public let version: String?

    enum CodingKeys: String, CodingKey { case ok, app, version }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        app = try c.decodeIfPresent(String.self, forKey: .app)
        version = try c.decodeIfPresent(String.self, forKey: .version)
    }
}

/// Antwort von POST /api/generate.
public struct GenerateResponse: Decodable, Sendable {
    public let ok: Bool
    public let error: String?
    public let assemblies: [Assembly]

    enum CodingKeys: String, CodingKey { case ok, error, assemblies }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        assemblies = try c.decodeIfPresent([Assembly].self, forKey: .assemblies) ?? []
    }

    public var errorCount: Int {
        assemblies.reduce(0) { $0 + $1.errors.count }
    }

    /// Exportieren ist nur erlaubt, wenn der Validator alles als CUT-READY bestätigt hat.
    public var canExport: Bool {
        ok && !assemblies.isEmpty && assemblies.allSatisfy { $0.ok && !$0.sheets.isEmpty }
    }
}

public struct Assembly: Decodable, Sendable, Identifiable {
    public var id: String { name }
    public let name: String
    public let ok: Bool
    public let summary: String
    public let report: String
    public let notes: [String]
    public let parts: Int
    public let joints: Int
    public let errors: [String]
    public let sheets: [SheetResult]

    enum CodingKeys: String, CodingKey { case name, ok, summary, report, notes, parts, joints, errors, sheets }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? "modell"
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        summary = try c.decodeIfPresent(String.self, forKey: .summary) ?? ""
        report = try c.decodeIfPresent(String.self, forKey: .report) ?? ""
        notes = try c.decodeIfPresent([String].self, forKey: .notes) ?? []
        parts = try c.decodeIfPresent(Int.self, forKey: .parts) ?? 0
        joints = try c.decodeIfPresent(Int.self, forKey: .joints) ?? 0
        errors = try c.decodeIfPresent([String].self, forKey: .errors) ?? []
        sheets = try c.decodeIfPresent([SheetResult].self, forKey: .sheets) ?? []
    }
}

public struct SheetResult: Decodable, Sendable, Identifiable {
    public var id: String { file }
    public let file: String
    public let svg: String
    public let width: Double
    public let height: Double
    public let parts: Int
    public let checked: Bool

    enum CodingKeys: String, CodingKey { case file, svg, width, height, parts, checked }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        file = try c.decodeIfPresent(String.self, forKey: .file) ?? "blatt.svg"
        svg = try c.decodeIfPresent(String.self, forKey: .svg) ?? ""
        width = try c.decodeIfPresent(Double.self, forKey: .width) ?? 0
        height = try c.decodeIfPresent(Double.self, forKey: .height) ?? 0
        parts = try c.decodeIfPresent(Int.self, forKey: .parts) ?? 0
        checked = try c.decodeIfPresent(Bool.self, forKey: .checked) ?? false
    }
}

public struct SaveResponse: Decodable, Sendable {
    public let ok: Bool
    public let outDir: String?
    public let files: [String]

    enum CodingKeys: String, CodingKey { case ok, files
        case outDir = "out_dir"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        outDir = try c.decodeIfPresent(String.self, forKey: .outDir)
        files = try c.decodeIfPresent([String].self, forKey: .files) ?? []
    }
}

/// Antworten mit Meldung und ggf. neuem Schema (Pakete installieren/entfernen, Kanal-Pakete).
public struct MessageResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let schema: Schema?

    enum CodingKeys: String, CodingKey { case ok, message, schema }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        message = try c.decodeIfPresent(String.self, forKey: .message)
        schema = try? c.decodeIfPresent(Schema.self, forKey: .schema)
    }
}

/// Antwort von POST /api/update-check.
public struct UpdateCheck: Decodable, Sendable {
    public let programm: ProgrammInfo
    public let pakete: [KanalPaket]
    public let updates: Int

    enum CodingKeys: String, CodingKey { case programm, pakete, updates }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        programm = try c.decode(ProgrammInfo.self, forKey: .programm)
        pakete = try c.decodeIfPresent([KanalPaket].self, forKey: .pakete) ?? []
        updates = try c.decodeIfPresent(Int.self, forKey: .updates) ?? 0
    }
}

public struct ProgrammInfo: Decodable, Sendable {
    public let installiert: String
    public let version: String
    public let neu: Bool
    public let datum: String
    public let hinweise: [String]
    public let grund: String

    enum CodingKeys: String, CodingKey { case installiert, version, neu, datum, hinweise, grund }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        installiert = try c.decodeIfPresent(String.self, forKey: .installiert) ?? ""
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        neu = try c.decodeIfPresent(Bool.self, forKey: .neu) ?? false
        datum = try c.decodeIfPresent(String.self, forKey: .datum) ?? ""
        hinweise = try c.decodeIfPresent([String].self, forKey: .hinweise) ?? []
        grund = (try? c.decodeIfPresent(String.self, forKey: .grund)) ?? ""
    }
}

public struct KanalPaket: Decodable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let version: String
    public let beschreibung: String
    public let installiert: String?
    public let status: String
    public let benoetigt: [String]
    public let groesse: Int

    enum CodingKeys: String, CodingKey { case id, name, version, beschreibung, installiert, status, benoetigt, groesse }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        beschreibung = try c.decodeIfPresent(String.self, forKey: .beschreibung) ?? ""
        installiert = try? c.decodeIfPresent(String.self, forKey: .installiert)
        status = try c.decodeIfPresent(String.self, forKey: .status) ?? ""
        benoetigt = (try? c.decodeIfPresent([String].self, forKey: .benoetigt)) ?? []
        groesse = (try? c.decodeIfPresent(Int.self, forKey: .groesse)) ?? 0
    }

    /// Installierbar, wenn noch nicht installiert oder eine neuere Version im Kanal liegt.
    public var installable: Bool {
        guard let installiert, !installiert.isEmpty else { return true }
        return installiert != version
    }
}

/// Antwort von POST /api/assistent-status.
public struct AssistentStatus: Decodable, Sendable {
    public let ok: Bool
    public let error: String?
    public let modelle: [String]

    enum CodingKeys: String, CodingKey { case ok, error, modelle }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        modelle = (try? c.decodeIfPresent([String].self, forKey: .modelle)) ?? []
    }
}

/// Antwort von POST /api/assistent: geprüfte Werte für das gewählte Modell.
public struct AssistentVorschlag: Decodable, Sendable {
    public let werte: [String: JSONValue]
    public let hinweis: String
    public let verworfen: [String]

    enum CodingKeys: String, CodingKey { case werte, hinweis, verworfen }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        werte = try c.decodeIfPresent([String: JSONValue].self, forKey: .werte) ?? [:]
        hinweis = try c.decodeIfPresent(String.self, forKey: .hinweis) ?? ""
        let raw = (try? c.decodeIfPresent([JSONValue].self, forKey: .verworfen)) ?? []
        verworfen = raw.map(\.displayText)
    }
}

/// Antwort von POST /api/bild.
public struct BildErgebnis: Decodable, Sendable {
    public let bild: String
    public let typ: String
    public let quelle: String
    public let modell: String
    public let kosten: Double

    enum CodingKeys: String, CodingKey { case bild, typ, quelle, modell, kosten }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        bild = try c.decode(String.self, forKey: .bild)
        typ = try c.decodeIfPresent(String.self, forKey: .typ) ?? "image/png"
        quelle = try c.decodeIfPresent(String.self, forKey: .quelle) ?? ""
        modell = try c.decodeIfPresent(String.self, forKey: .modell) ?? ""
        kosten = try c.decodeIfPresent(Double.self, forKey: .kosten) ?? 0
    }

    public var data: Data? { Data(base64Encoded: bild) }

    public var dateiendung: String {
        switch typ {
        case "image/svg+xml": return "svg"
        case "image/jpeg": return "jpg"
        case "image/webp": return "webp"
        default: return "png"
        }
    }
}

/// Antwort von POST /api/motiv-import und /api/motiv-entfernen.
public struct MotivResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let id: String?
}
