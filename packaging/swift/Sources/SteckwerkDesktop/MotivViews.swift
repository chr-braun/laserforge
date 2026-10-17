import SteckwerkCore
import SwiftUI

/// Kleines Vorschaubild eines Motivs aus seinen Flächen (wie in der Weboberfläche: y nach oben).
@MainActor
struct MotivThumbnail: View {
    let motiv: Motiv

    var body: some View {
        Canvas { context, size in
            let inset = size.width * 0.08
            let scale = min(size.width, size.height) - 2 * inset
            let center = CGPoint(x: size.width / 2, y: size.height / 2)
            func map(_ p: SteckwerkCore.Point) -> CGPoint {
                CGPoint(x: center.x + p.x * scale, y: center.y - p.y * scale)
            }
            var fill = Path()
            for flaeche in motiv.flaechen {
                for ring in [flaeche.aussen] + flaeche.loecher where ring.count > 2 {
                    fill.move(to: map(ring[0]))
                    for p in ring.dropFirst() { fill.addLine(to: map(p)) }
                    fill.closeSubpath()
                }
            }
            context.fill(fill, with: .color(.primary), style: FillStyle(eoFill: true))
            var lines = Path()
            for line in motiv.linien where line.count > 1 {
                lines.move(to: map(line[0]))
                for p in line.dropFirst() { lines.addLine(to: map(p)) }
            }
            context.stroke(lines, with: .color(.primary), lineWidth: 1)
        }
        .accessibilityLabel(motiv.name)
    }
}

/// Motiv-Auswahl als Raster mit Vorschaubildern.
@MainActor
struct MotivGridPicker: View {
    @Binding var selection: String
    let motive: [Motiv]

    private let columns = [GridItem(.adaptive(minimum: 64, maximum: 84), spacing: 8)]

    var body: some View {
        if motive.isEmpty {
            Text("Keine Motive in der Bibliothek")
                .foregroundStyle(.secondary)
        } else {
            ScrollView {
                LazyVGrid(columns: columns, spacing: 8) {
                    ForEach(motive) { motiv in
                        Button {
                            selection = motiv.id
                        } label: {
                            VStack(spacing: 2) {
                                MotivThumbnail(motiv: motiv)
                                    .frame(width: 48, height: 48)
                                Text(motiv.name)
                                    .font(.caption2)
                                    .lineLimit(1)
                            }
                            .padding(4)
                            .frame(maxWidth: .infinity)
                            .background(
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(selection == motiv.id ? Theme.accent.opacity(0.18) : Color.clear)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(selection == motiv.id ? Theme.accent : Color.primary.opacity(0.1))
                            )
                        }
                        .buttonStyle(.plain)
                        .help(motiv.name)
                    }
                }
                .padding(2)
            }
            .frame(maxHeight: 220)
        }
    }
}

/// Liste der platzierten Motive (Typ `motive`): Motiv, Lage, Größe, Drehung, Spiegeln, Art.
@MainActor
struct MotivPlacementEditor: View {
    let param: Param
    @Binding var value: JSONValue
    let motive: [Motiv]
    @State var picking: Int?

    private var placements: [MotivPlacement] { MotivPlacement.list(value) }
    private var limit: Int { param.max.map { Int($0) } ?? 12 }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(param.label)
                Spacer()
                Button {
                    var list = placements
                    var neu = list.last ?? MotivPlacement(json: param.defaultValue.arrayValue?.first ?? .object([:]))
                    if neu.motivID.isEmpty { neu.motivID = motive.first?.id ?? "" }
                    neu.x += 5
                    neu.y -= 5
                    list.append(neu)
                    value = MotivPlacement.json(list)
                } label: {
                    Label("Motiv hinzufügen", systemImage: "plus")
                }
                .disabled(placements.count >= limit || motive.isEmpty)
            }
            ForEach(Array(placements.enumerated()), id: \.offset) { index, placement in
                placementCard(index: index, placement: placement)
            }
        }
        .sheet(item: Binding(get: { picking.map(PickIndex.init) }, set: { picking = $0?.id })) { pick in
            VStack(alignment: .leading) {
                Text("Motiv wählen").font(.headline)
                MotivGridPicker(selection: Binding(
                    get: { placements.indices.contains(pick.id) ? placements[pick.id].motivID : "" },
                    set: { id in
                        update(pick.id) { $0.motivID = id }
                        picking = nil
                    }
                ), motive: motive)
                .frame(minHeight: 240)
                HStack {
                    Spacer()
                    Button("Fertig") { picking = nil }
                        .keyboardShortcut(.defaultAction)
                }
            }
            .padding()
            .frame(width: 460)
        }
    }

    private func placementCard(index: Int, placement: MotivPlacement) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Button {
                    picking = index
                } label: {
                    HStack {
                        if let motiv = motive.first(where: { $0.id == placement.motivID }) {
                            MotivThumbnail(motiv: motiv).frame(width: 28, height: 28)
                            Text(motiv.name)
                        } else {
                            Text(placement.motivID.isEmpty ? "Motiv wählen" : placement.motivID)
                        }
                    }
                }
                .buttonStyle(.borderless)
                Spacer()
                Button(role: .destructive) {
                    var list = placements
                    list.remove(at: index)
                    value = MotivPlacement.json(list)
                } label: {
                    Image(systemName: "trash")
                }
                .buttonStyle(.borderless)
                .help("Motiv entfernen")
            }
            Grid(alignment: .leading, horizontalSpacing: 8, verticalSpacing: 4) {
                GridRow {
                    numberField(index, "x", placement.x, unit: "mm") { p, v in p.x = v }
                    numberField(index, "y", placement.y, unit: "mm") { p, v in p.y = v }
                }
                GridRow {
                    numberField(index, "Größe", placement.groesse, unit: "mm") { p, v in p.groesse = max(1, v) }
                    numberField(index, "Drehung", placement.drehung, unit: "°") { p, v in p.drehung = v }
                }
            }
            HStack {
                Toggle("Spiegeln", isOn: Binding(
                    get: { placement.spiegeln },
                    set: { flag in update(index) { $0.spiegeln = flag } }
                ))
                if !param.arten.isEmpty {
                    Picker("Art", selection: Binding(
                        get: { placement.art },
                        set: { art in update(index) { $0.art = art } }
                    )) {
                        ForEach(param.arten, id: \.self) { option in
                            Text(option.label).tag(option.value.stringValue ?? option.label)
                        }
                    }
                    .fixedSize()
                }
            }
        }
        .padding(8)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.primary.opacity(0.04)))
    }

    private func numberField(_ index: Int, _ label: String, _ current: Double, unit: String,
                             apply: @escaping (inout MotivPlacement, Double) -> Void) -> some View {
        HStack(spacing: 4) {
            Text(label).frame(width: 56, alignment: .leading)
            TextField(label, value: Binding(
                get: { current },
                set: { v in update(index) { apply(&$0, v) } }
            ), format: .number.precision(.fractionLength(0...1)))
            .labelsHidden()
            .frame(width: 64)
            .textFieldStyle(.roundedBorder)
            Text(unit).foregroundStyle(.secondary)
        }
    }

    private func update(_ index: Int, _ change: (inout MotivPlacement) -> Void) {
        var list = placements
        guard list.indices.contains(index) else { return }
        change(&list[index])
        value = MotivPlacement.json(list)
    }
}

private struct PickIndex: Identifiable {
    let id: Int
}
