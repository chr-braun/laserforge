import SwiftUI

struct PreferencesView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var selectedProvider = "ollama"
    @State private var openrouterKey = ""
    @State private var chatgptKey = ""
    @State private var statusText = ""

    var body: some View {
        VStack(spacing: 20) {
            Text("Einstellungen")
                .font(.title2)
                .fontWeight(.bold)

            Form {
                Section(header: Text("Bild-Anbieter")) {
                    Picker("Standard-Anbieter", selection: $selectedProvider) {
                        Text("Ollama (lokal)").tag("ollama")
                        Text("OpenRouter (Cloud)").tag("openrouter")
                        Text("ChatGPT (OpenAI)").tag("chatgpt")
                    }
                }

                Section(header: Text("API-Schlüssel"), footer: Text("Schlüssel werden von der Engine im Schlüsselbund gespeichert und nie angezeigt.")) {
                    SecureField("OpenRouter-Schlüssel", text: $openrouterKey)
                    SecureField("ChatGPT-Schlüssel", text: $chatgptKey)
                }
            }
            .padding()

            if !statusText.isEmpty {
                Text(statusText)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 12) {
                Spacer()
                Button("Abbrechen") {
                    clearKeyFields()
                    NSApp.keyWindow?.close()
                }
                Button("Speichern") {
                    Task { await save() }
                }
                .keyboardShortcut(.return, modifiers: .command)
            }
            .padding()
        }
        .frame(minWidth: 420, minHeight: 320)
    }

    private func save() async {
        guard let bridge = engineManager.bridge else {
            statusText = "Engine läuft nicht."
            return
        }
        do {
            try await bridge.bildEinstellungen(quelle: selectedProvider, key: nil)
            if !openrouterKey.isEmpty {
                try await bridge.bildEinstellungen(quelle: "openrouter", key: openrouterKey)
            }
            if !chatgptKey.isEmpty {
                try await bridge.bildEinstellungen(quelle: "chatgpt", key: chatgptKey)
            }
            clearKeyFields()
            statusText = "Gespeichert."
        } catch {
            clearKeyFields()
            statusText = error.localizedDescription
        }
    }

    private func clearKeyFields() {
        openrouterKey = ""
        chatgptKey = ""
    }
}

#Preview {
    PreferencesView()
        .environmentObject(EngineManager())
}
