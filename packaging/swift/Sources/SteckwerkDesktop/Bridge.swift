import Foundation

class Bridge {
    private let baseURL: URL
    private let session: URLSession

    init(baseURL: URL = URL(string: "http://127.0.0.1:5000")!) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    func ping(timeout: TimeInterval = 15) async throws -> Bool {
        let url = baseURL.appendingPathComponent("api/ping")
        var request = URLRequest(url: url)
        request.timeoutInterval = timeout

        do {
            let (data, response) = try await session.data(for: request)
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                return true
            }
            return false
        } catch {
            return false
        }
    }

    func schema() async throws -> SchemaResponse {
        return try await get(endpoint: "api/schema", responseType: SchemaResponse.self)
    }

    func generate(modelId: String, params: [String: AnyCodable]) async throws -> GenerateResponse {
        let payload: [String: AnyCodable] = [
            "model": AnyCodable(modelId),
            "params": AnyCodable(params)
        ]
        return try await post(endpoint: "api/generate", payload: payload, responseType: GenerateResponse.self)
    }

    func save(svgContent: String, reportContent: String) async throws -> SaveResponse {
        let payload: [String: AnyCodable] = [
            "svg": AnyCodable(svgContent),
            "report": AnyCodable(reportContent)
        ]
        return try await post(endpoint: "api/save", payload: payload, responseType: SaveResponse.self)
    }

    func openFolder() async throws {
        _ = try await get(endpoint: "api/open-folder", responseType: EmptyResponse.self)
    }

    func paketInstallieren(kanal: String) async throws -> PaketResponse {
        let payload: [String: AnyCodable] = ["kanal": AnyCodable(kanal)]
        return try await post(endpoint: "api/paket-installieren", payload: payload, responseType: PaketResponse.self)
    }

    func paketEntfernen(paketId: String) async throws -> PaketResponse {
        let payload: [String: AnyCodable] = ["paket_id": AnyCodable(paketId)]
        return try await post(endpoint: "api/paket-entfernen", payload: payload, responseType: PaketResponse.self)
    }

    func updateCheck() async throws -> UpdateCheckResponse {
        return try await get(endpoint: "api/update-check", responseType: UpdateCheckResponse.self)
    }

    func updateProgramm() async throws -> UpdateResponse {
        return try await post(endpoint: "api/update-programm", payload: [:], responseType: UpdateResponse.self)
    }

    func assistent(modelId: String, request: String) async throws -> AssistentResponse {
        let payload: [String: AnyCodable] = [
            "model": AnyCodable(modelId),
            "request": AnyCodable(request)
        ]
        return try await post(endpoint: "api/assistent", payload: payload, responseType: AssistentResponse.self)
    }

    func bildGenerieren(prompt: String, quelle: String) async throws -> BildResponse {
        let payload: [String: AnyCodable] = [
            "prompt": AnyCodable(prompt),
            "quelle": AnyCodable(quelle)
        ]
        return try await post(endpoint: "api/bild", payload: payload, responseType: BildResponse.self)
    }

    func bye() async throws {
        _ = try await post(endpoint: "api/bye", payload: [:], responseType: EmptyResponse.self)
    }

    private func get<T: Decodable>(endpoint: String, responseType: T.Type) async throws -> T {
        let url = baseURL.appendingPathComponent(endpoint)
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw BridgeError.invalidResponse
        }

        let decoder = JSONDecoder()
        return try decoder.decode(T.self, from: data)
    }

    private func post<T: Decodable>(endpoint: String, payload: [String: AnyCodable], responseType: T.Type) async throws -> T {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let jsonPayload = try JSONSerialization.data(withJSONObject: encodeAnyCodable(payload))
        request.httpBody = jsonPayload

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw BridgeError.invalidResponse
        }

        let decoder = JSONDecoder()
        return try decoder.decode(T.self, from: data)
    }

    private func encodeAnyCodable(_ value: [String: AnyCodable]) -> [String: Any] {
        var result: [String: Any] = [:]
        for (key, anyCodable) in value {
            result[key] = anyCodable.value
        }
        return result
    }
}

enum BridgeError: LocalizedError {
    case invalidResponse
    case decodingError
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Engine antwortet nicht richtig"
        case .decodingError:
            return "Fehler beim Parsen der Antwort"
        case .networkError(let error):
            return "Netzwerkfehler: \(error.localizedDescription)"
        }
    }
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
            let mapped = dictVal.mapValues { AnyCodable($0) }
            try container.encode(mapped)
        } else {
            try container.encodeNil()
        }
    }
}

struct SchemaResponse: Codable {
    let models: [ModelSchema]
    let config: ConfigSchema
    let motive: [MotiveSchema]
    let pakete: [PaketSchema]
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
    let status: String
    let fehler: [String]?
    let warnungen: [String]?
    let data: GenerateData?
}

struct GenerateData: Codable {
    let svg: String?
    let geometrie: GeometrieData?
    let teile: [[String: AnyCodable]]?
}

struct GeometrieData: Codable {
    let blattbreite: Double?
    let blatthoehe: Double?
    let schnittbreite: Double?
    let schnitthoehe: Double?
}

struct SaveResponse: Codable {
    let erfolg: Bool
    let pfad: String?
}

struct EmptyResponse: Codable {}

struct PaketResponse: Codable {
    let erfolg: Bool
    let meldung: String?
}

struct UpdateCheckResponse: Codable {
    let verfuegbar: Bool
    let version: String?
    let url: String?
}

struct UpdateResponse: Codable {
    let erfolg: Bool
}

struct AssistentResponse: Codable {
    let erfolg: Bool
    let werte: [String: AnyCodable]?
    let fehler: String?
}

struct BildResponse: Codable {
    let erfolg: Bool
    let data: String?
    let fehler: String?
}
