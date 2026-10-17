import SwiftUI

struct PackagesView: View {
    @ObservedObject var bridge: Bridge
    @State var packages: [String] = []
    @State var showFileImporter = false
    @State var selectedFile: URL?

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            Text("Pakete")
                .font(.title2)

            HStack {
                Button(action: { showFileImporter = true }) {
                    Image(systemName: "plus.circle.fill")
                    Text("Paket installieren")
                }
                .buttonStyle(.bordered)

                Spacer()
            }

            List {
                ForEach(packages, id: \.self) { pkg in
                    HStack {
                        Text(pkg)
                        Spacer()
                        Button(action: { removePackage(pkg) }) {
                            Image(systemName: "trash.fill")
                                .foregroundColor(.red)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            Spacer()
        }
        .padding()
        .background(Color.warmBg)
        .fileImporter(
            isPresented: $showFileImporter,
            allowedContentTypes: [.data],
            onCompletion: { result in
                if case .success(let url) = result {
                    installPackageFromFile(url)
                }
            }
        )
    }

    private func installPackageFromFile(_ url: URL) {
        // Placeholder for API call
    }

    private func removePackage(_ name: String) {
        // Placeholder for API call
    }
}

struct KIView: View {
    @ObservedObject var bridge: Bridge
    @State var selectedProvider = "ollama"
    @State var apiKey = ""
    @State var assistantResponse = ""

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            Text("KI-Assistent")
                .font(.title2)

            Section(header: Text("Anbieter")) {
                Picker("Anbieter", selection: $selectedProvider) {
                    Text("Ollama").tag("ollama")
                    Text("OpenRouter").tag("openrouter")
                    Text("ChatGPT").tag("chatgpt")
                }
                .pickerStyle(.segmented)
            }
            .padding()
            .background(Color.white)
            .cornerRadius(Theme.cornerRadius)

            if selectedProvider != "ollama" {
                Section(header: Text("API-Schlüssel")) {
                    SecureField("Schlüssel", text: $apiKey)
                }
                .padding()
                .background(Color.white)
                .cornerRadius(Theme.cornerRadius)
            }

            Button(action: { askAssistant() }) {
                HStack {
                    Image(systemName: "sparkles")
                    Text("Assistent befragen")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.accent)
                .foregroundColor(.white)
                .cornerRadius(Theme.cornerRadius)
            }

            if !assistantResponse.isEmpty {
                VStack(alignment: .leading) {
                    Text("Antwort:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Text(assistantResponse)
                        .padding()
                        .background(Color.white)
                        .cornerRadius(Theme.cornerRadius)
                }
            }

            Spacer()
        }
        .padding()
        .background(Color.warmBg)
    }

    private func askAssistant() {
        // Placeholder
    }
}

struct MaterialView: View {
    @ObservedObject var bridge: Bridge
    @State var thickness = 3.0
    @State var kerf = 0.3
    @State var scale = 1.0

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            Text("Material & Einstellungen")
                .font(.title2)

            Form {
                Section(header: Text("Material")) {
                    HStack {
                        Text("Materialdicke")
                        Stepper(value: $thickness, in: 0.1...10, step: 0.1) {
                            TextField("", value: $thickness, format: .number)
                        }
                        Text("mm")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("Schnittspalt (Kerf)")
                        Stepper(value: $kerf, in: 0...1, step: 0.05) {
                            TextField("", value: $kerf, format: .number)
                        }
                        Text("mm")
                            .foregroundColor(.secondary)
                    }
                }

                Section(header: Text("Anpassung")) {
                    HStack {
                        Text("Maßstab")
                        Stepper(value: $scale, in: 0.5...2, step: 0.1) {
                            TextField("", value: $scale, format: .number)
                        }
                        Text("×")
                            .foregroundColor(.secondary)
                    }
                }
            }

            Spacer()
        }
        .padding()
        .background(Color.warmBg)
    }
}

struct AppUpdateView: View {
    @ObservedObject var bridge: Bridge
    @State var updateAvailable = false
    @State var currentVersion = "1.0.0"

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            Text("Updates")
                .font(.title2)

            Section(header: Text("Version")) {
                HStack {
                    Text("Installierte Version")
                    Spacer()
                    Text(currentVersion)
                        .foregroundColor(.secondary)
                }
            }
            .padding()
            .background(Color.white)
            .cornerRadius(Theme.cornerRadius)

            Button(action: { checkForUpdates() }) {
                HStack {
                    Image(systemName: "arrow.down.circle.fill")
                    Text("Nach Updates suchen")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.accent)
                .foregroundColor(.white)
                .cornerRadius(Theme.cornerRadius)
            }

            if updateAvailable {
                VStack(alignment: .leading, spacing: Theme.spacing8) {
                    HStack {
                        Image(systemName: "arrow.up.circle.fill")
                            .foregroundColor(.green)
                        Text("Update verfügbar!")
                            .font(.headline)
                    }

                    Button(action: { installUpdate() }) {
                        HStack {
                            Image(systemName: "icloud.and.arrow.down.fill")
                            Text("Update installieren")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green.opacity(0.2))
                        .foregroundColor(.green)
                        .cornerRadius(Theme.cornerRadius)
                    }
                }
                .padding()
                .background(Color.green.opacity(0.05))
                .cornerRadius(Theme.cornerRadius)
            }

            Spacer()
        }
        .padding()
        .background(Color.warmBg)
    }

    private func checkForUpdates() {
        // Placeholder
    }

    private func installUpdate() {
        // Placeholder
    }
}

#Preview {
    TabView {
        PackagesView(bridge: Bridge())
            .tabItem { Label("Pakete", systemImage: "cube.box.fill") }

        KIView(bridge: Bridge())
            .tabItem { Label("KI", systemImage: "sparkles") }
    }
}
