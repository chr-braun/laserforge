import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public enum EngineError: LocalizedError, Equatable {
    case notRunning
    case invalidResponse
    case server(String)

    public var errorDescription: String? {
        switch self {
        case .notRunning: return "Die Engine läuft nicht."
        case .invalidResponse: return "Die Engine hat unverständlich geantwortet."
        case .server(let message): return message
        }
    }
}

private struct ErrorEnvelope: Decodable {
    let ok: Bool?
    let error: String?
}

/// Schicht unter dem Client: schickt eine Anfrage und liefert Daten und HTTP-Status.
public protocol HTTPTransport: Sendable {
    func send(_ request: URLRequest) async throws -> (Data, Int)
}

public struct URLSessionTransport: HTTPTransport {
    private let session: URLSession

    public init(timeout: TimeInterval = 300) {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = timeout
        config.timeoutIntervalForResource = timeout
        config.connectionProxyDictionary = [:]
        self.session = URLSession(configuration: config)
    }

    public func send(_ request: URLRequest) async throws -> (Data, Int) {
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw EngineError.invalidResponse
        }
        return (data, http.statusCode)
    }
}

/// Spricht die lokale HTTP-API der Python-Engine (webui.py) an.
public struct EngineClient: Sendable {
    public static let clientID = "steckwerk-desktop"

    public let baseURL: URL
    private let transport: HTTPTransport

    public init(port: Int, transport: HTTPTransport = URLSessionTransport()) {
        self.baseURL = URL(string: "http://127.0.0.1:\(port)")!
        self.transport = transport
    }

    public init(baseURL: URL, transport: HTTPTransport) {
        self.baseURL = baseURL
        self.transport = transport
    }

    // MARK: Anfragen bauen und auswerten (ohne Netz testbar)

    public func makeRequest(_ path: String, body: [String: JSONValue]?, timeout: TimeInterval? = nil) throws -> URLRequest {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        if let timeout { request.timeoutInterval = timeout }
        if let body {
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("1", forHTTPHeaderField: "X-Steckwerk")
            request.httpBody = try JSONEncoder().encode(body)
        } else {
            request.httpMethod = "GET"
        }
        return request
    }

    /// Wertet eine Antwort aus: Fehlermeldungen der Engine ({"ok": false, "error": …}) werden zu `EngineError.server`.
    public static func decode<T: Decodable>(_ type: T.Type, data: Data, status: Int) throws -> T {
        let envelope = try? JSONDecoder().decode(ErrorEnvelope.self, from: data)
        if !(200..<300).contains(status) || envelope?.ok == false {
            if let message = envelope?.error, !message.isEmpty {
                throw EngineError.server(message)
            }
            if !(200..<300).contains(status) {
                throw EngineError.server("Die Engine meldet Fehler \(status).")
            }
        }
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw EngineError.invalidResponse
        }
    }

    private func call<T: Decodable>(_ path: String, _ body: [String: JSONValue]?, as type: T.Type,
                                    timeout: TimeInterval? = nil) async throws -> T {
        let request = try makeRequest(path, body: body, timeout: timeout)
        let (data, status) = try await transport.send(request)
        return try Self.decode(type, data: data, status: status)
    }

    // MARK: Lebenszyklus

    public func ping(timeout: TimeInterval = 2) async throws -> PingResponse {
        try await call("api/ping", ["client": .string(Self.clientID)], as: PingResponse.self, timeout: timeout)
    }

    public func bye() async throws {
        _ = try await call("api/bye", ["client": .string(Self.clientID)], as: PingResponse.self, timeout: 2)
    }

    public func quit() async throws {
        _ = try await call("api/quit", [:], as: PingResponse.self, timeout: 2)
    }

    // MARK: Modelle bauen

    public func schema() async throws -> Schema {
        try await call("api/schema", nil, as: Schema.self)
    }

    public func generate(model: String, params: [String: JSONValue], config: [String: JSONValue]) async throws -> GenerateResponse {
        let body: [String: JSONValue] = ["model": .string(model), "params": .object(params), "config": .object(config)]
        let request = try makeRequest("api/generate", body: body)
        let (data, status) = try await transport.send(request)
        // Ein ungültiges Modell ist kein Netzfehler: die Antwort trägt ok=false und eine Meldung.
        if (200..<300).contains(status), let response = try? JSONDecoder().decode(GenerateResponse.self, from: data) {
            return response
        }
        return try Self.decode(GenerateResponse.self, data: data, status: status)
    }

    public func save(model: String, params: [String: JSONValue], config: [String: JSONValue]) async throws -> SaveResponse {
        let body: [String: JSONValue] = ["model": .string(model), "params": .object(params), "config": .object(config)]
        return try await call("api/save", body, as: SaveResponse.self)
    }

    public func openFolder() async throws {
        _ = try await call("api/open-folder", [:], as: PingResponse.self)
    }

    // MARK: Pakete und Updates

    public func paketInstallieren(data: Data) async throws -> MessageResponse {
        try await call("api/paket-installieren", ["data": .string(data.base64EncodedString())], as: MessageResponse.self)
    }

    public func paketEntfernen(id: String) async throws -> MessageResponse {
        try await call("api/paket-entfernen", ["id": .string(id)], as: MessageResponse.self)
    }

    public func updateCheck() async throws -> UpdateCheck {
        try await call("api/update-check", [:], as: UpdateCheck.self, timeout: 60)
    }

    public func kanalPaketInstallieren(id: String) async throws -> MessageResponse {
        try await call("api/update-paket", ["id": .string(id)], as: MessageResponse.self)
    }

    public func alleKanalPaketeInstallieren() async throws -> MessageResponse {
        try await call("api/update-paket", ["alle": .bool(true)], as: MessageResponse.self)
    }

    // MARK: KI

    public func assistentStatus() async throws -> AssistentStatus {
        let request = try makeRequest("api/assistent-status", body: [:], timeout: 10)
        let (data, _) = try await transport.send(request)
        guard let status = try? JSONDecoder().decode(AssistentStatus.self, from: data) else {
            throw EngineError.invalidResponse
        }
        return status
    }

    public func assistent(model: String, beschreibung: String, params: [String: JSONValue]) async throws -> AssistentVorschlag {
        let body: [String: JSONValue] = ["model": .string(model), "beschreibung": .string(beschreibung), "params": .object(params)]
        return try await call("api/assistent", body, as: AssistentVorschlag.self)
    }

    public func bild(beschreibung: String, stil: String, quelle: String) async throws -> BildErgebnis {
        let body: [String: JSONValue] = ["beschreibung": .string(beschreibung), "stil": .string(stil), "quelle": .string(quelle)]
        return try await call("api/bild", body, as: BildErgebnis.self)
    }

    /// Bild-Einstellungen ändern. Ein Schlüssel geht nur an die lokale Engine, die ihn im Schlüsselbund ablegt;
    /// zurück kommt er nie.
    public func bildEinstellungen(quelle: String? = nil, key: String? = nil, limit: Double? = nil) async throws {
        var body: [String: JSONValue] = [:]
        if let quelle { body["quelle"] = .string(quelle) }
        if let key { body["key"] = .string(key) }
        if let limit { body["limit"] = .double(limit) }
        _ = try await call("api/bild-einstellungen", body, as: PingResponse.self)
    }

    public func motivImport(data: Data, filename: String, name: String) async throws -> MotivResponse {
        let body: [String: JSONValue] = ["data": .string(data.base64EncodedString()), "filename": .string(filename),
                                         "name": .string(name), "invert": .bool(false)]
        return try await call("api/motiv-import", body, as: MotivResponse.self)
    }
}
