import SteckwerkCore
import SwiftUI

@MainActor
struct ContentView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        Group {
            switch model.engineState {
            case .running:
                MainSplitView()
            case .starting:
                StartingView()
            case .failed:
                EngineFailureView()
            }
        }
        .background(Theme.background)
        .tint(Theme.accent)
        .alert(item: $model.alert) { alert in
            Alert(title: Text(alert.title), message: Text(alert.message), dismissButton: .default(Text("OK")))
        }
    }
}

@MainActor
private struct StartingView: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
            Text("Engine wird gestartet …")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

@MainActor
private struct EngineFailureView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Engine startet nicht", systemImage: "exclamationmark.triangle.fill")
                .font(.title2.bold())
                .foregroundStyle(Theme.error)
            Text(model.engineError ?? "Unbekannter Fehler")
                .textSelection(.enabled)
            if !model.engineDetails.isEmpty {
                DisclosureGroup("Details") {
                    ScrollView {
                        Text(model.engineDetails)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: 240)
                }
            }
            Button("Erneut versuchen") {
                model.restartEngine()
            }
            .keyboardShortcut(.defaultAction)
        }
        .padding(32)
        .frame(maxWidth: 640)
        .card()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

@MainActor
private struct MainSplitView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationSplitView {
            SidebarView()
                .navigationSplitViewColumnWidth(min: 200, ideal: 240, max: 320)
        } detail: {
            DetailView()
        }
        .toolbar {
            ToolbarItem(placement: .status) {
                EngineStatusBadge()
            }
        }
    }
}

@MainActor
private struct SidebarView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        List(selection: $model.selection) {
            if let schema = model.schema {
                ForEach(schema.sidebarGroups) { group in
                    Section(group.label) {
                        ForEach(group.models) { entry in
                            Text(entry.info.label)
                                .tag(SidebarItem.model(entry.id))
                                .help(entry.info.desc)
                        }
                    }
                }
            }
            Section("Werkstatt") {
                Label("Pakete", systemImage: "shippingbox").tag(SidebarItem.pakete)
                Label("KI", systemImage: "wand.and.stars").tag(SidebarItem.ki)
                Label("Material", systemImage: "ruler").tag(SidebarItem.material)
                Label("Updates", systemImage: "arrow.down.circle").tag(SidebarItem.updates)
            }
        }
        .listStyle(.sidebar)
    }
}

@MainActor
private struct DetailView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        switch model.selection {
        case .model(let id):
            if let info = model.schema?.models[id] {
                HSplitView {
                    ParameterForm(modelID: id, info: info)
                        .frame(minWidth: 320, idealWidth: 400, maxWidth: 560)
                    BuildView(modelID: id)
                        .frame(minWidth: 420, maxWidth: .infinity)
                }
            } else {
                placeholder("Dieses Modell gibt es nicht mehr.")
            }
        case .pakete:
            PackagesView()
        case .ki:
            KIView()
        case .material:
            MaterialView()
        case .updates:
            AppUpdateView()
        case nil:
            placeholder("Links ein Modell wählen.")
        }
    }

    private func placeholder(_ text: String) -> some View {
        Text(text)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Engine-Status in der Werkzeugleiste: lädt / läuft / gestoppt.
@MainActor
struct EngineStatusBadge: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .help(model.engineVersion.map { "Engine \($0)" } ?? "Engine")
    }

    private var text: String {
        switch model.engineState {
        case .starting: return "Engine lädt"
        case .running: return model.isBuilding ? "Engine baut …" : "Engine läuft"
        case .failed: return "Engine gestoppt"
        }
    }

    private var color: Color {
        switch model.engineState {
        case .starting: return Theme.warning
        case .running: return Theme.ok
        case .failed: return Theme.error
        }
    }
}
