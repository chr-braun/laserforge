import SwiftUI

struct ModelListView: View {
    @EnvironmentObject var engineManager: EngineManager
    @State private var expandedGroups: Set<String> = []

    var body: some View {
        List(selection: .constant(engineManager.selectedModel?.id)) {
            if let schema = engineManager.schema {
                let groupedModels = Dictionary(grouping: schema.models, by: { $0.group })

                ForEach(Array(groupedModels.keys).sorted(), id: \.self) { group in
                    Section(header: Text(group).font(.headline)) {
                        ForEach(groupedModels[group] ?? [], id: \.id) { model in
                            ModelRow(model: model)
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    engineManager.selectedModel = model
                                }
                                .background(
                                    engineManager.selectedModel?.id == model.id ?
                                    Color.accentColor.opacity(0.1) : Color.clear
                                )
                        }
                    }
                }

                Section("Pakete") {
                    NavigationLink(destination: PackagesView()) {
                        Label("Paketmanager", systemImage: "cube.box.fill")
                    }
                }

                Section("KI") {
                    NavigationLink(destination: KIView()) {
                        Label("KI-Einstellungen", systemImage: "wand.and.stars")
                    }
                }

                Section("Material") {
                    NavigationLink(destination: MaterialView()) {
                        Label("Materialparameter", systemImage: "square.2.layers.3d.down.forward")
                    }
                }

                Section("Updates") {
                    NavigationLink(destination: AppUpdateView()) {
                        Label("Nach Updates suchen", systemImage: "arrow.down.circle")
                    }
                }
            }
        }
        .listStyle(.sidebar)
    }
}

struct ModelRow: View {
    let model: ModelSchema

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(model.label)
                .font(.headline)
            Text(model.desc)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    List {
        ModelRow(model: ModelSchema(
            id: "test",
            label: "Testmodell",
            desc: "Ein Testmodell zur Vorschau",
            group: "Demo",
            params: []
        ))
    }
    .listStyle(.sidebar)
}
