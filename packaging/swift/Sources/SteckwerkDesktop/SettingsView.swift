import SteckwerkCore
import SwiftUI

/// Einstellungen (⌘,): Material und KI-Anbieter.
@MainActor
struct SettingsView: View {
    var body: some View {
        TabView {
            MaterialView()
                .tabItem { Label("Material", systemImage: "ruler") }
            KISettingsView()
                .tabItem { Label("KI-Anbieter", systemImage: "key") }
        }
        .frame(width: 560, height: 600)
    }
}

/// Bildquelle, Schlüssel und Monatslimit. Schlüssel gehen nur an die lokale Engine, die sie im Schlüsselbund
/// ablegt; die App speichert sie nirgends und zeigt nur an, ob einer hinterlegt ist.
@MainActor
struct KISettingsView: View {
    @EnvironmentObject var model: AppModel
    @State var openrouterKey = ""
    @State var chatgptKey = ""
    @State var limit: Double = 0
    @State var message: String?
    @State var busy = false

    private var bilder: BildSettings? { model.schema?.assistent?.bilder }

    var body: some View {
        Form {
            Section {
                Picker("Standard für Bilder", selection: Binding(
                    get: { bilder?.quelle ?? "ollama" },
                    set: { neu in perform { try await $0.bildEinstellungen(quelle: neu) } }
                )) {
                    Text("Ollama (lokal, kostenlos)").tag("ollama")
                    Text("OpenRouter (Cloud)").tag("openrouter")
                    Text("ChatGPT (OpenAI)").tag("chatgpt")
                }
            } header: {
                Text("Bild-Anbieter")
            } footer: {
                Text("Der Assistent für Werte-Vorschläge nutzt immer Ollama auf diesem Rechner.")
            }

            keySection(title: "OpenRouter", provider: "openrouter", text: $openrouterKey)
            keySection(title: "ChatGPT (OpenAI)", provider: "chatgpt", text: $chatgptKey)

            Section {
                LabeledContent("Monatslimit") {
                    HStack {
                        TextField("Limit", value: $limit, format: .number.precision(.fractionLength(0...2)))
                            .labelsHidden()
                            .frame(width: 80)
                            .textFieldStyle(.roundedBorder)
                        Text("$ (0 = ohne Limit)").foregroundStyle(.secondary)
                        Button("Übernehmen") {
                            let value = limit
                            perform { try await $0.bildEinstellungen(limit: value) }
                        }
                    }
                }
            } header: {
                Text("Kosten")
            }

            if busy || message != nil {
                Section {
                    HStack {
                        if busy { ProgressView().controlSize(.small) }
                        if let message { Text(message) }
                    }
                }
            }
        }
        .formStyle(.grouped)
        .onAppear { limit = bilder?.limit ?? 0 }
        .onDisappear {
            openrouterKey = ""
            chatgptKey = ""
        }
    }

    private func keySection(title: String, provider: String, text: Binding<String>) -> some View {
        Section {
            LabeledContent("Status") {
                if bilder?.keys[provider] == true {
                    Label("Schlüssel hinterlegt", systemImage: "checkmark.seal").foregroundStyle(Theme.ok)
                } else {
                    Label("kein Schlüssel", systemImage: "key").foregroundStyle(.secondary)
                }
            }
            SecureField("Neuer Schlüssel", text: text)
            HStack {
                Button("Speichern") {
                    let key = text.wrappedValue.trimmingCharacters(in: .whitespacesAndNewlines)
                    text.wrappedValue = ""
                    guard !key.isEmpty else { return }
                    saveKey(key, for: provider)
                }
                .disabled(text.wrappedValue.isEmpty || busy)
                Button("Schlüssel löschen", role: .destructive) {
                    saveKey("", for: provider)
                }
                .disabled(bilder?.keys[provider] != true || busy)
            }
        } header: {
            Text(title)
        }
    }

    /// Schlüssel für einen Anbieter setzen, ohne den Standard-Anbieter zu ändern.
    private func saveKey(_ key: String, for provider: String) {
        let keep = bilder?.quelle ?? "ollama"
        perform { client in
            try await client.bildEinstellungen(quelle: provider, key: key)
            if keep != provider {
                try await client.bildEinstellungen(quelle: keep)
            }
        }
    }

    private func perform(_ action: @escaping (EngineClient) async throws -> Void) {
        guard let client = model.client else {
            message = "Die Engine läuft nicht."
            return
        }
        busy = true
        message = nil
        Task {
            defer { busy = false }
            do {
                try await action(client)
                await model.reloadSchema()
                message = "Gespeichert."
            } catch {
                message = error.localizedDescription
            }
        }
    }
}
