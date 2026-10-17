import SwiftUI

@main
struct SteckwerkApp: App {
    @StateObject var bridge = Bridge()
    @State var schema: Schema?
    @State var selectedModel: Schema.Model?
    @State var showError = false
    @State var showExportDialog = false

    var body: some Scene {
        WindowGroup {
            if bridge.isConnected, let schema = schema {
                MainView(bridge: bridge, schema: schema, selectedModel: $selectedModel)
                    .frame(minWidth: 1200, minHeight: 800)
            } else if let error = bridge.lastError {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 48))
                        .foregroundColor(.red)

                    Text("Engine startet nicht")
                        .font(.title)

                    Text(error)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)

                    Button("Erneut versuchen") {
                        Task {
                            await initEngine()
                        }
                    }
                    .buttonStyle(.bordered)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.warmBg)
            } else {
                VStack {
                    ProgressView()
                    Text("Steckwerk Engine wird gestartet...")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.warmBg)
            }
        }
        .onAppear {
            Task {
                await initEngine()
            }
        }
        .commands {
            CommandGroup(replacing: .appMenu) {
                Button("Über Steckwerk Desktop") { }
                    .keyboardShortcut("?", modifiers: [.command, .shift])

                Divider()

                Button("Einstellungen") { }
                    .keyboardShortcut(",", modifiers: .command)
            }

            CommandGroup(replacing: .appSettings) { }

            CommandGroup(replacing: .newItem) {
                Button("Exportieren") {
                    showExportDialog = true
                }
                .keyboardShortcut("e", modifiers: .command)

                Button("Ordner öffnen") { }
                    .keyboardShortcut("o", modifiers: .command)
            }

            CommandGroup(replacing: .undoRedo) { }

            CommandGroup(replacing: .pasteboard) {
                Button("Bauen & Prüfen") { }
                    .keyboardShortcut("b", modifiers: .command)
            }
        }
    }

    private func initEngine() async {
        let success = await bridge.startEngine()

        if success {
            if let schema = await bridge.getSchema() {
                DispatchQueue.main.async {
                    self.schema = schema
                    self.selectedModel = schema.models.first
                }
            }
        }
    }
}

struct MainView: View {
    @ObservedObject var bridge: Bridge
    let schema: Schema
    @Binding var selectedModel: Schema.Model?

    @State var showExportDialog = false
    @State var modelParams: [String: AnyCodable] = [:]
    @State var lastGenerateResponse: GenerateResponse?

    var body: some View {
        NavigationSplitView {
            List(selection: $selectedModel) {
                Section("Modelle") {
                    ForEach(schema.models) { model in
                        NavigationLink(value: model) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(model.label)
                                    .font(.body)
                                Text(model.desc)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .tag(model)
                    }
                }

                Section("Werkzeuge") {
                    NavigationLink(destination: PackagesView(bridge: bridge)) {
                        Label("Pakete", systemImage: "cube.box.fill")
                    }

                    NavigationLink(destination: KIView(bridge: bridge)) {
                        Label("KI-Assistent", systemImage: "sparkles")
                    }

                    NavigationLink(destination: MaterialView(bridge: bridge)) {
                        Label("Material", systemImage: "square.fill")
                    }

                    NavigationLink(destination: AppUpdateView(bridge: bridge)) {
                        Label("Updates", systemImage: "arrow.up.circle.fill")
                    }
                }
            }
            .navigationTitle("Steckwerk")
        } detail: {
            if let model = selectedModel {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        ParameterForm(
                            parameters: model.params,
                            values: $modelParams
                        )

                        Button(action: { Task { await buildModel(model) } }) {
                            HStack {
                                Image(systemName: "hammer.fill")
                                Text("Bauen & Prüfen")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.accent)
                            .foregroundColor(.white)
                            .cornerRadius(Theme.cornerRadius)
                        }

                        if let response = lastGenerateResponse {
                            BuildView(response: response)
                        }

                        Spacer()
                    }
                    .padding()
                }
                .background(Color.warmBg)
            } else {
                VStack {
                    Text("Modell auswählen")
                        .foregroundColor(.secondary)
                }
            }
        }
        .onAppear {
            if let model = selectedModel {
                initializeParams(for: model)
            }
        }
    }

    private func initializeParams(for model: Schema.Model) {
        var params: [String: AnyCodable] = [:]
        for param in model.params {
            params[param.key] = param.default
        }
        modelParams = params
    }

    private func buildModel(_ model: Schema.Model) async {
        let response = await bridge.generate(modelKey: model.id, params: modelParams)
        if let response = response {
            DispatchQueue.main.async {
                self.lastGenerateResponse = response
            }
        }
    }
}

#Preview {
    SteckwerkApp()
}
