import AppKit
import SteckwerkCore
import SwiftUI

/// KI: Assistent schlägt Werte vor (Ollama), Bildmodell zeichnet ein Motiv (Ollama, OpenRouter oder ChatGPT).
@MainActor
struct KIView: View {
    @EnvironmentObject var model: AppModel

    @State var assistentModel = ""
    @State var beschreibung = ""
    @State var assistentBusy = false
    @State var assistentStatus: AssistentStatus?
    @State var assistentText: String?

    @State var bildBeschreibung = ""
    @State var stil = "silhouette"
    @State var quelle = ""
    @State var bildBusy = false
    @State var bild: BildErgebnis?
    @State var bildText: String?
    @State var motivName = ""

    private var bilder: BildSettings? { model.schema?.assistent?.bilder }

    var body: some View {
        Form {
            assistentSection
            bildSection
        }
        .formStyle(.grouped)
        .navigationTitle("KI")
        .onAppear {
            if assistentModel.isEmpty {
                assistentModel = model.resultModelID ?? (model.schema?.models["wichtelhaus"] != nil ? "wichtelhaus" : "")
            }
            if quelle.isEmpty { quelle = bilder?.quelle ?? "ollama" }
        }
    }

    // MARK: Assistent

    private var assistentSection: some View {
        Section {
            Picker("Modell", selection: $assistentModel) {
                ForEach(model.schema?.sidebarGroups ?? []) { group in
                    ForEach(group.models) { entry in
                        Text(entry.info.label).tag(entry.id)
                    }
                }
            }
            LabeledContent("Wunsch") {
                TextField("z. B. kleines Haus mit zwei Fenstern und Kamin", text: $beschreibung, axis: .vertical)
                    .lineLimit(2...5)
                    .labelsHidden()
                    .textFieldStyle(.roundedBorder)
            }
            HStack {
                Button("Werte vorschlagen") {
                    Task { await suggest() }
                }
                .disabled(assistentBusy || assistentModel.isEmpty || beschreibung.trimmingCharacters(in: .whitespaces).isEmpty)
                Button("Ollama prüfen") {
                    Task { await checkOllama() }
                }
                .disabled(assistentBusy)
                if assistentBusy { ProgressView().controlSize(.small) }
            }
            if let status = assistentStatus {
                Label(status.ok ? "Ollama läuft – Modelle: \(status.modelle.joined(separator: ", "))"
                                : (status.error ?? "Ollama ist nicht erreichbar"),
                      systemImage: status.ok ? "checkmark.circle" : "exclamationmark.triangle")
                    .foregroundStyle(status.ok ? Theme.ok : Theme.warning)
                    .font(.caption)
            }
            if let assistentText {
                Text(assistentText)
                    .textSelection(.enabled)
                Button("Zum Modell") {
                    model.selection = .model(assistentModel)
                }
            }
        } header: {
            Text("Assistent")
        } footer: {
            Text("Der Assistent läuft über Ollama auf diesem Rechner. Die Engine prüft jeden Vorschlag wie eine Eingabe.")
        }
    }

    private func checkOllama() async {
        guard let client = model.client else { return }
        assistentBusy = true
        defer { assistentBusy = false }
        assistentStatus = try? await client.assistentStatus()
    }

    private func suggest() async {
        guard let client = model.client else { return }
        assistentBusy = true
        assistentText = nil
        defer { assistentBusy = false }
        do {
            let vorschlag = try await client.assistent(model: assistentModel, beschreibung: beschreibung,
                                                       params: model.values(for: assistentModel))
            let changed = model.applySuggestion(vorschlag.werte, to: assistentModel)
            var lines: [String] = []
            lines.append(changed.isEmpty ? "Keine Werte geändert." : "Geändert: \(changed.joined(separator: ", "))")
            if !vorschlag.hinweis.isEmpty { lines.append(vorschlag.hinweis) }
            if !vorschlag.verworfen.isEmpty { lines.append("Verworfen: \(vorschlag.verworfen.joined(separator: ", "))") }
            assistentText = lines.joined(separator: "\n")
        } catch {
            assistentText = error.localizedDescription
        }
    }

    // MARK: Motiv zeichnen

    private var bildSection: some View {
        Section {
            LabeledContent("Motiv") {
                TextField("z. B. Reh im Sprung", text: $bildBeschreibung)
                    .labelsHidden()
                    .textFieldStyle(.roundedBorder)
            }
            Picker("Stil", selection: $stil) {
                let stile = bilder?.stile ?? []
                if stile.isEmpty {
                    Text("Silhouette").tag("silhouette")
                }
                ForEach(stile, id: \.self) { option in
                    Text(option.label).tag(option.value.stringValue ?? option.label)
                }
            }
            Picker("Anbieter", selection: $quelle) {
                Text("Ollama (lokal)").tag("ollama")
                Text("OpenRouter").tag("openrouter")
                Text("ChatGPT (OpenAI)").tag("chatgpt")
            }
            if quelle != "ollama" && bilder?.keys[quelle] != true {
                Label("Für diesen Anbieter fehlt noch der Schlüssel – unter Einstellungen (⌘,) → KI-Anbieter eintragen.",
                      systemImage: "key")
                    .font(.caption)
                    .foregroundStyle(Theme.warning)
            }
            HStack {
                Button("Zeichnen") {
                    Task { await draw() }
                }
                .disabled(bildBusy || bildBeschreibung.trimmingCharacters(in: .whitespaces).isEmpty)
                if bildBusy { ProgressView().controlSize(.small) }
            }
            if let bild, let data = bild.data {
                HStack(alignment: .top, spacing: Theme.spacing) {
                    if let image = NSImage(data: data) {
                        Image(nsImage: image)
                            .resizable()
                            .interpolation(.high)
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 180, height: 180)
                            .background(Color.white)
                            .clipShape(RoundedRectangle(cornerRadius: 6))
                    } else {
                        Text("Bild erhalten (\(bild.typ))")
                            .frame(width: 180, height: 180)
                            .background(Color.primary.opacity(0.05))
                    }
                    VStack(alignment: .leading, spacing: 8) {
                        Text("\(bild.modell) · \(bild.quelle)" + (bild.kosten > 0 ? String(format: " · %.3f $", bild.kosten) : ""))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        TextField("Name des Motivs", text: $motivName)
                            .textFieldStyle(.roundedBorder)
                        Button("Als Motiv übernehmen") {
                            Task { await importMotiv(bild) }
                        }
                        .disabled(bildBusy)
                    }
                }
            }
            if let bildText {
                Text(bildText).textSelection(.enabled)
            }
        } header: {
            Text("Motiv zeichnen")
        } footer: {
            Text("Bei OpenRouter und ChatGPT geht die Beschreibung an den Anbieter und kostet Guthaben; das Monatslimit stellst du in den Einstellungen ein.")
        }
    }

    private func draw() async {
        guard let client = model.client else { return }
        bildBusy = true
        bildText = nil
        bild = nil
        defer { bildBusy = false }
        do {
            bild = try await client.bild(beschreibung: bildBeschreibung, stil: stil, quelle: quelle)
            if motivName.isEmpty { motivName = bildBeschreibung }
        } catch {
            bildText = error.localizedDescription
        }
    }

    private func importMotiv(_ bild: BildErgebnis) async {
        guard let client = model.client, let raw = bild.data else { return }
        bildBusy = true
        defer { bildBusy = false }
        do {
            let (data, ext) = try Self.importable(raw, typ: bild.typ, ext: bild.dateiendung)
            let response = try await client.motivImport(data: data, filename: "ki-motiv.\(ext)", name: motivName)
            await model.reloadSchema()
            bildText = response.message ?? "Motiv übernommen"
        } catch {
            bildText = error.localizedDescription
        }
    }

    /// Die Engine liest SVG und PNG; JPEG und WebP werden vorher in PNG umgewandelt.
    static func importable(_ data: Data, typ: String, ext: String) throws -> (Data, String) {
        if typ == "image/svg+xml" || typ == "image/png" { return (data, ext) }
        guard let image = NSImage(data: data),
              let tiff = image.tiffRepresentation,
              let rep = NSBitmapImageRep(data: tiff),
              let png = rep.representation(using: .png, properties: [:]) else {
            throw EngineError.server("Das Bild ließ sich nicht in PNG umwandeln.")
        }
        return (png, "png")
    }
}
