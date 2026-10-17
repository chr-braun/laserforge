import Foundation
import AppKit

enum EngineStatus {
    case stopped
    case starting
    case running
    case error
}

class EngineManager: NSObject, ObservableObject {
    @Published var engineStatus = EngineStatus.stopped
    @Published var engineError: String?
    @Published var schema: SchemaResponse?
    @Published var selectedModel: ModelSchema?
    @Published var buildStatus = ""
    @Published var canExport = false
    @Published var lastSVG: String?
    @Published var lastReport: String?

    private var process: Process?
    private(set) var bridge: Bridge?
    private var port: Int = 0
    private var portPipe: Pipe?

    override init() {
        super.init()
    }

    func start() {
        engineStatus = .starting
        engineError = nil

        Task {
            do {
                try await ensureEngineRunning()
                engineStatus = .running
                try await loadSchema()
                if let models = schema?.models, !models.isEmpty {
                    await MainActor.run {
                        self.selectedModel = models.first { $0.id == "wichtelhaus" } ?? models[0]
                    }
                }
            } catch {
                await MainActor.run {
                    self.engineStatus = .error
                    self.engineError = error.localizedDescription
                }
            }
        }
    }

    func stop() {
        Task {
            try? await bridge?.bye()
            if let process = process, process.isRunning {
                process.terminate()
                let deadline = Date().addingTimeInterval(3)
                while process.isRunning && Date() < deadline {
                    usleep(100_000)
                }
                if process.isRunning {
                    process.interrupt()
                }
            }
        }
    }

    func restart() {
        stop()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.start()
        }
    }

    private func ensureEngineRunning() async throws {
        let bridge = Bridge(baseURL: URL(string: "http://127.0.0.1:5000")!)

        if try await bridge.ping() {
            self.bridge = bridge
            return
        }

        try startProcess()

        for _ in 0..<150 {
            if try await bridge.ping(timeout: 0.1) {
                self.bridge = bridge
                return
            }
            try await Task.sleep(nanoseconds: 100_000_000)
        }

        throw NSError(domain: "EngineError", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "Engine konnte nicht in 15 Sekunden gestartet werden"
        ])
    }

    private func startProcess() throws {
        let pythonPath = ProcessInfo.processInfo.environment["PYTHONPATH"] ?? ""
        let repoRoot = URL(fileURLWithPath: ProcessInfo.processInfo.environment["STECKWERK_ROOT"]
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("steckwerk").path)

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = [
            repoRoot.appendingPathComponent("webui.py").path,
            "--port", "5000"
        ]
        process.environment = ProcessInfo.processInfo.environment
        process.environment?["PYTHONPATH"] = pythonPath

        let pipe = Pipe()
        process.standardError = pipe

        try process.run()
        self.process = process
        self.portPipe = pipe
    }

    private func loadSchema() async throws {
        guard let bridge = bridge else {
            throw NSError(domain: "EngineError", code: 1, userInfo: [
                NSLocalizedDescriptionKey: "Bridge nicht initialisiert"
            ])
        }

        let response = try await bridge.schema()
        await MainActor.run {
            self.schema = response
        }
    }

    func buildAction() {
        guard let selectedModel = selectedModel else { return }

        Task {
            await MainActor.run {
                self.buildStatus = "Wird gebaut…"
            }

            do {
                guard let bridge = bridge else { return }

                var params: [String: AnyCodable] = [:]
                for param in selectedModel.params {
                    params[param.key] = param.default
                }

                let response = try await bridge.generate(modelId: selectedModel.id, params: params)

                var statusText = ""
                if let fehler = response.fehler, !fehler.isEmpty {
                    statusText = "❌ \(fehler.count) Fehler"
                } else {
                    statusText = "✓ 0 Fehler"
                }

                if let warnungen = response.warnungen, !warnungen.isEmpty {
                    statusText += ", ⚠️ \(warnungen.count) Warnungen"
                }

                await MainActor.run {
                    self.buildStatus = statusText
                    self.lastSVG = response.data?.svg
                    self.canExport = response.status == "ok"
                }
            } catch {
                await MainActor.run {
                    self.buildStatus = "Fehler: \(error.localizedDescription)"
                }
            }
        }
    }

    func exportAction() {
        let dialog = NSSavePanel()
        dialog.title = "SVG exportieren"
        dialog.allowedContentTypes = [.svg]
        dialog.nameFieldStringValue = "steckwerk-export.svg"

        if dialog.runModal() == .OK, let url = dialog.url {
            Task {
                do {
                    guard let svg = lastSVG else { return }
                    try svg.write(to: url, atomically: true, encoding: .utf8)
                } catch {
                    print("Export fehler: \(error)")
                }
            }
        }
    }

    func openFolderAction() {
        Task {
            do {
                guard let bridge = bridge else { return }
                try await bridge.openFolder()
            } catch {
                print("Ordner-Fehler: \(error)")
            }
        }
    }
}
