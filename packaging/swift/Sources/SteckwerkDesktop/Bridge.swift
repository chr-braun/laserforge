import Foundation

class Bridge: ObservableObject {
    @Published var isConnected = false
    @Published var lastError: String?

    var engineProcess: Process?
    var baseURL: URL?
    private let session = URLSession.shared

    func startEngine(pythonPath: String = "python3") async -> Bool {
        let pipe = Pipe()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")

        let port = findFreePort() ?? 8765
        process.arguments = [pythonPath, "webui.py", "--port", "\(port)"]
        process.currentDirectoryURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        process.standardError = pipe

        self.baseURL = URL(string: "http://127.0.0.1:\(port)")
        self.engineProcess = process

        do {
            try process.run()

            await waitForPing(maxRetries: 15)
            return isConnected
        } catch {
            lastError = "Engine-Start fehlgeschlagen: \(error.localizedDescription)"
            return false
        }
    }

    private func findFreePort() -> Int? {
        for port in 8765...9765 {
            let socket = socket(AF_INET, SOCK_STREAM, 0)
            guard socket >= 0 else { continue }

            var addr = sockaddr_in()
            addr.sin_family = sa_family_t(AF_INET)
            addr.sin_addr.s_addr = inet_addr("127.0.0.1")
            addr.sin_port = in_port_t(port).bigEndian

            if bind(socket, (UnsafeMutableRawPointer(&addr) as! UnsafeMutablePointer<sockaddr>), socklen_t(MemoryLayout<sockaddr_in>.size)) == 0 {
                close(socket)
                return port
            }
            close(socket)
        }
        return nil
    }

    private func waitForPing(maxRetries: Int) async {
        for i in 0..<maxRetries {
            if await ping() {
                DispatchQueue.main.async { self.isConnected = true }
                return
            }
            try? await Task.sleep(nanoseconds: 1_000_000_000)
        }

        let stderrData = (engineProcess?.standardError as? Pipe)?.fileHandleForReading.readDataToEndOfFile()
        let stderr = String(data: stderrData ?? Data(), encoding: .utf8) ?? "Unbekannter Fehler"
        DispatchQueue.main.async {
            self.isConnected = false
            self.lastError = "Engine antwortet nicht nach 15 Sekunden.\nStderr: \(stderr)"
        }
    }

    func ping() async -> Bool {
        guard let url = baseURL?.appendingPathComponent("api/ping") else { return false }

        do {
            let (_, response) = try await session.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }

    func getSchema() async -> Schema? {
        guard let url = baseURL?.appendingPathComponent("api/schema") else { return nil }

        do {
            let (data, _) = try await session.data(from: url)
            let decoder = JSONDecoder()
            return try decoder.decode(Schema.self, from: data)
        } catch {
            DispatchQueue.main.async { self.lastError = "Schema abrufen fehlgeschlagen: \(error)" }
            return nil
        }
    }

    func generate(modelKey: String, params: [String: AnyCodable]) async -> GenerateResponse? {
        guard let url = baseURL?.appendingPathComponent("api/generate") else { return nil }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: Any] = [
            "modell": modelKey,
            "params": params.mapValues { $0.value }
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            let (data, _) = try await session.data(for: request)
            let decoder = JSONDecoder()
            return try decoder.decode(GenerateResponse.self, from: data)
        } catch {
            DispatchQueue.main.async { self.lastError = "Generierung fehlgeschlagen: \(error)" }
            return nil
        }
    }

    func saveExport(svgContent: String, reportContent: String, to folder: URL) async -> Bool {
        do {
            let svgURL = folder.appendingPathComponent("design.svg")
            let reportURL = folder.appendingPathComponent("bericht.txt")
            try svgContent.write(to: svgURL, atomically: true, encoding: .utf8)
            try reportContent.write(to: reportURL, atomically: true, encoding: .utf8)
            return true
        } catch {
            DispatchQueue.main.async { self.lastError = "Export speichern fehlgeschlagen: \(error)" }
            return false
        }
    }

    func shutdown() {
        if let process = engineProcess, process.isRunning {
            process.terminate()

            DispatchQueue.global().asyncAfter(deadline: .now() + 3) {
                if self.engineProcess?.isRunning == true {
                    self.engineProcess?.interrupt()
                }
            }
        }
    }

    deinit {
        shutdown()
    }
}

struct Schema: Codable {
    struct Model: Codable, Identifiable {
        let id: String
        let label: String
        let desc: String
        let group: String
        let params: [Parameter]

        enum CodingKeys: String, CodingKey {
            case id = "key"
            case label, desc, group, params
        }
    }

    struct Parameter: Codable, Identifiable {
        let id: String
        let label: String
        let type: String
        let key: String
        let `default`: AnyCodable
        let options: [OptionValue]?
        let min: Double?
        let max: Double?
        let step: Double?
        let unit: String?
        let help: String?
        let section: String?

        enum CodingKeys: String, CodingKey {
            case id = "key"
            case label, type, key, `default`, options, min, max, step, unit, help, section
        }
    }

    struct OptionValue: Codable {
        let label: String
        let value: AnyCodable
    }

    let models: [Model]
    let config: ConfigInfo
    let motive: [MotiveInfo]
    let pakete: [PaketInfo]
}

struct ConfigInfo: Codable {
    let kerf: Double?
    let material_thickness: Double?
    let scale: Double?
}

struct MotiveInfo: Codable, Identifiable {
    let id: String
    let label: String
    let thumb: String?

    enum CodingKeys: String, CodingKey {
        case id = "key"
        case label, thumb
    }
}

struct PaketInfo: Codable {
    let channel: String
    let packages: [String]
}

struct GenerateResponse: Codable {
    let success: Bool
    let polylines: [[PolylinePoint]]?
    let svgContent: String?
    let validationResult: ValidationResult?
    let error: String?
}

struct PolylinePoint: Codable {
    let x: Double
    let y: Double
    let layer: String?
}

struct ValidationResult: Codable {
    let valid: Bool
    let errors: [String]
    let warnings: [String]
}

enum AnyCodable: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)
    case null

    var value: Any {
        switch self {
        case .string(let s): return s
        case .int(let i): return i
        case .double(let d): return d
        case .bool(let b): return b
        case .null: return NSNull()
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if container.decodeNil() {
            self = .null
        } else if let bool = try? container.decode(Bool.self) {
            self = .bool(bool)
        } else if let int = try? container.decode(Int.self) {
            self = .int(int)
        } else if let double = try? container.decode(Double.self) {
            self = .double(double)
        } else if let string = try? container.decode(String.self) {
            self = .string(string)
        } else {
            self = .null
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let s): try container.encode(s)
        case .int(let i): try container.encode(i)
        case .double(let d): try container.encode(d)
        case .bool(let b): try container.encode(b)
        case .null: try container.encodeNil()
        }
    }
}
