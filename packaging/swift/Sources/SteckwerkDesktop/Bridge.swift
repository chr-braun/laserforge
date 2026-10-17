import Foundation

class Bridge {
    private let baseURL: URL
    private let session: URLSession
    private static let clientName = "steckwerk-desktop"

    init(baseURL: URL = URL(string: "http://127.0.0.1:5000")!) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    func ping(timeout: TimeInterval = 15) async throws {
        _ = try await send(endpoint: "api/ping", payload: ["client": Self.clientName], timeout: timeout)
    }

    func schema() async throws -> SchemaResponse {
        let data = try await send(endpoint: "api/schema", payload: nil)
        return try JSONDecoder().decode(SchemaResponse.self, from: data)
    }

    func generate(modelId: String, params: [String: Any]) async throws -> GenerateResponse {
        let data = try await send(endpoint: "api/generate", payload: ["model": modelId, "params": params])
        return try JSONDecoder().decode(GenerateResponse.self, from: data)
    }

    func openFolder() async throws {
        _ = try await send(endpoint: "api/open-folder", payload: ["client": Self.clientName])
    }

    func updateCheck() async throws -> UpdateCheckResponse {
        let data = try await send(endpoint: "api/update-check", payload: [:])
        return try JSONDecoder().decode(UpdateCheckResponse.self, from: data)
    }

    func updateProgramm() async throws {
        _ = try await send(endpoint: "api/update-programm", payload: [:])
    }

    func bildEinstellungen(quelle: String?, key: String?) async throws {
        var payload: [String: Any] = [:]
        if let quelle { payload["quelle"] = quelle }
        if let key { payload["key"] = key }
        _ = try await send(endpoint: "api/bild-einstellungen", payload: payload)
    }

    func bye() async throws {
        _ = try await send(endpoint: "api/bye", payload: ["client": Self.clientName], timeout: 3)
    }

    private func send(endpoint: String, payload: [String: Any]?, timeout: TimeInterval? = nil) async throws -> Data {
        var request = URLRequest(url: baseURL.appendingPathComponent(endpoint))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("1", forHTTPHeaderField: "X-Steckwerk")
        if let timeout { request.timeoutInterval = timeout }
        request.httpBody = try JSONSerialization.data(withJSONObject: payload ?? [:])

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw BridgeError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            let message = (try? JSONDecoder().decode(ErrorBody.self, from: data))?.error
            throw BridgeError.server(message ?? "Engine meldet Fehler \(http.statusCode)")
        }
        return data
    }
}

enum BridgeError: LocalizedError {
    case invalidResponse
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Engine antwortet nicht richtig"
        case .server(let message):
            return message
        }
    }
}

struct ErrorBody: Decodable {
    let error: String?
}

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let intVal = try? container.decode(Int.self) {
            self.value = intVal
        } else if let doubleVal = try? container.decode(Double.self) {
            self.value = doubleVal
        } else if let stringVal = try? container.decode(String.self) {
            self.value = stringVal
        } else if let boolVal = try? container.decode(Bool.self) {
            self.value = boolVal
        } else if let arrayVal = try? container.decode([AnyCodable].self) {
            self.value = arrayVal.map { $0.value }
        } else if let dictVal = try? container.decode([String: AnyCodable].self) {
            self.value = dictVal.mapValues { $0.value }
        } else {
            self.value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let intVal = value as? Int {
            try container.encode(intVal)
        } else if let doubleVal = value as? Double {
            try container.encode(doubleVal)
        } else if let stringVal = value as? String {
            try container.encode(stringVal)
        } else if let boolVal = value as? Bool {
            try container.encode(boolVal)
        } else if let arrayVal = value as? [Any] {
            try container.encode(arrayVal.map { AnyCodable($0) })
        } else if let dictVal = value as? [String: Any] {
            try container.encode(dictVal.mapValues { AnyCodable($0) })
        } else {
            try container.encodeNil()
        }
    }
}

struct SchemaResponse: Codable {
    let models: [ModelSchema]
    let config: ConfigSchema?
    let motive: [MotiveSchema]?
    let pakete: [PaketSchema]?
}

struct ModelSchema: Codable {
    let id: String
    let label: String
    let desc: String
    let group: String
    let params: [ParamSchema]
}

struct ParamSchema: Codable {
    let type: String
    let key: String
    let label: String
    let `default`: AnyCodable
    let options: [String]?
    let min: Double?
    let max: Double?
    let step: Double?
    let unit: String?
    let help: String?
    let section: String?
}

struct ConfigSchema: Codable {
    let language: String?
    let theme: String?
}

struct MotiveSchema: Codable {
    let id: String
    let label: String
    let data: String?
}

struct PaketSchema: Codable {
    let id: String
    let label: String
    let kanal: String?
    let version: String?
}

struct GenerateResponse: Codable {
    let status: String?
    let fehler: [String]?
    let warnungen: [String]?
    let data: GenerateData?
}

struct GenerateData: Codable {
    let svg: String?
}

struct UpdateCheckResponse: Codable {
    let verfuegbar: Bool?
    let version: String?
    let url: String?
}
