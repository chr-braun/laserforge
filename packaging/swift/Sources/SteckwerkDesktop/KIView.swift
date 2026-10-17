import SwiftUI

struct KIView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var selectedProvider = "ollama"
    @State private var apiKey = ""
    @State private var prompt = ""
    @State private var result = ""
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 16) {
            Text("KI-Einstellungen und Assistent")
                .font(.title2)
                .fontWeight(.bold)

            Section(header: Text("KI-Anbieter").font(.headline)) {
                Picker("Anbieter", selection: $selectedProvider) {
                    Text("Ollama").tag("ollama")
                    Text("OpenRouter").tag("openrouter")
                    Text("ChatGPT").tag("chatgpt")
                }
                .pickerStyle(.segmented)

                SecureField("API-Schlüssel", text: $apiKey)
                    .textFieldStyle(.roundedBorder)
            }

            Section(header: Text("Assistent").font(.headline)) {
                TextEditor(text: $prompt)
                    .frame(minHeight: 80)
                    .border(Color.gray, width: 0.5)
                    .cornerRadius(4)

                Button(action: {
                    callAssistant()
                }) {
                    if isLoading {
                        ProgressView()
                    } else {
                        Text("Werte generieren")
                    }
                }
                .disabled(isLoading)

                if !result.isEmpty {
                    VStack(alignment: .leading) {
                        Text("Ergebnis:")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(result)
                            .font(.monospaced(.body)())
                            .padding()
                            .background(Color(nsColor: Theme.cardColor))
                            .cornerRadius(4)
                    }
                }
            }

            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }

    private func callAssistant() {
        isLoading = true
        Task {
            do {
                guard let model = engineManager.selectedModel else { return }
                let response = try await engineManager.bridge?.assistent(modelId: model.id, request: prompt)

                if response?.erfolg == true {
                    if let werte = response?.werte {
                        result = "Erfolg: \(werte)"
                    }
                } else {
                    result = response?.fehler ?? "Unbekannter Fehler"
                }
            } catch {
                result = "Fehler: \(error.localizedDescription)"
            }
            await MainActor.run {
                isLoading = false
            }
        }
    }
}

#Preview {
    KIView()
        .environmentObject(EngineManager())
}
