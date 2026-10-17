import SwiftUI

struct PreferencesView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var selectedProvider = "ollama"
    @State private var openrouterKey = ""
    @State private var chatgptKey = ""

    var body: some View {
        VStack(spacing: 20) {
            Text("Einstellungen")
                .font(.title2)
                .fontWeight(.bold)

            Form {
                Section(header: Text("KI-Anbieter")) {
                    Picker("Standard-Anbieter", selection: $selectedProvider) {
                        Text("Ollama (lokal)").tag("ollama")
                        Text("OpenRouter (Cloud)").tag("openrouter")
                        Text("ChatGPT (OpenAI)").tag("chatgpt")
                    }
                }

                Section(header: Text("API-Schlüssel")) {
                    SecureField("OpenRouter-Schlüssel", text: $openrouterKey)
                    SecureField("ChatGPT-Schlüssel", text: $chatgptKey)
                }

                Section(header: Text("Allgemein")) {
                    Toggle("Bildgen mit Textausgabe debuggen", isOn: .constant(false))
                }
            }
            .padding()

            HStack(spacing: 12) {
                Spacer()
                Button("Abbrechen") {
                    NSApp.keyWindow?.close()
                }
                Button("Speichern") {
                    savePreferences()
                    NSApp.keyWindow?.close()
                }
                .keyboardShortcut(.return, modifiers: .command)
            }
            .padding()
        }
        .frame(minWidth: 400, minHeight: 300)
    }

    private func savePreferences() {
        let defaults = UserDefaults.standard
        defaults.set(selectedProvider, forKey: "kiAnbieter")
        defaults.set(openrouterKey, forKey: "openrouterKey")
        defaults.set(chatgptKey, forKey: "chatgptKey")
    }
}

#Preview {
    PreferencesView()
        .environmentObject(EngineManager())
}
