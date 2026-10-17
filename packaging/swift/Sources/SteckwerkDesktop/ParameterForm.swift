import SteckwerkCore
import SwiftUI

/// Dynamisches Formular aus schema.models[].params – `section` wird zu einer eigenen Section.
@MainActor
struct ParameterForm: View {
    @EnvironmentObject var model: AppModel
    let modelID: String
    let info: ModelInfo

    var body: some View {
        let current = model.values(for: modelID)
        Form {
            Section {
                VStack(alignment: .leading, spacing: 4) {
                    Text(info.label)
                        .font(.title2.bold())
                    if !info.desc.isEmpty {
                        Text(info.desc)
                            .font(.callout)
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            ForEach(ParameterLogic.sections(info.params)) { section in
                let visible = section.params.filter { ParameterLogic.isVisible($0, values: current) }
                if !visible.isEmpty {
                    Section {
                        ForEach(visible) { param in
                            ParamRow(param: param, value: model.binding(for: param, in: modelID))
                        }
                    } header: {
                        Text(section.title ?? "Allgemein")
                    }
                }
            }
            Section {
                Button("Auf Standardwerte zurücksetzen") {
                    model.resetValues(for: modelID)
                }
            }
        }
        .formStyle(.grouped)
    }
}

/// Ein Eingabeelement passend zum Parametertyp.
@MainActor
struct ParamRow: View {
    @EnvironmentObject var model: AppModel
    let param: Param
    @Binding var value: JSONValue

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            control
            if !param.help.isEmpty && param.kind != .bool {
                Text(param.help)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    @ViewBuilder
    private var control: some View {
        switch param.kind {
        case .number, .int:
            NumberRow(param: param, value: $value)
        case .bool:
            Toggle(param.label, isOn: Binding(
                get: { value.boolValue ?? false },
                set: { value = .bool($0) }
            ))
            .help(param.help)
        case .select:
            Picker(param.label, selection: Binding(
                get: { param.options.firstIndex { $0.value.looselyEquals(value) } ?? 0 },
                set: { index in
                    if param.options.indices.contains(index) { value = param.options[index].value }
                }
            )) {
                ForEach(Array(param.options.enumerated()), id: \.offset) { index, option in
                    Text(option.label).tag(index)
                }
            }
        case .text:
            LabeledContent(param.label) {
                TextField(param.label, text: Binding(
                    get: { value.stringValue ?? "" },
                    set: { value = .string($0) }
                ), axis: .vertical)
                .lineLimit(1...4)
                .labelsHidden()
                .textFieldStyle(.roundedBorder)
            }
        case .motiv:
            VStack(alignment: .leading) {
                Text(param.label)
                MotivGridPicker(selection: Binding(
                    get: { value.stringValue ?? "" },
                    set: { value = .string($0) }
                ), motive: model.schema?.motive ?? [])
            }
        case .motive:
            MotivPlacementEditor(param: param, value: $value, motive: model.schema?.motive ?? [])
        case .unknown:
            LabeledContent(param.label) {
                Text("Typ „\(param.type)“ wird hier noch nicht unterstützt")
                    .foregroundStyle(.secondary)
            }
        }
    }
}

/// Zahl mit Stepper und Einheit.
@MainActor
struct NumberRow: View {
    let param: Param
    @Binding var value: JSONValue

    private var number: Binding<Double> {
        Binding(
            get: { value.doubleValue ?? param.defaultValue.doubleValue ?? 0 },
            set: { value = ParameterLogic.coerce(.double($0), for: param) }
        )
    }

    private var range: ClosedRange<Double> {
        let low = param.min ?? -1_000_000
        let high = Swift.max(param.max ?? 1_000_000, low)
        return low...high
    }

    private var step: Double {
        if let step = param.step, step > 0 { return step }
        return param.kind == .int ? 1 : 0.1
    }

    var body: some View {
        LabeledContent(param.label) {
            HStack(spacing: 6) {
                TextField(param.label, value: number,
                          format: .number.precision(.fractionLength(0...ParameterLogic.decimals(for: param))))
                    .labelsHidden()
                    .multilineTextAlignment(.trailing)
                    .frame(width: 80)
                    .textFieldStyle(.roundedBorder)
                Stepper(param.label, value: number, in: range, step: step)
                    .labelsHidden()
                if !param.unit.isEmpty {
                    Text(param.unit)
                        .foregroundStyle(.secondary)
                        .frame(minWidth: 24, alignment: .leading)
                }
            }
        }
    }
}
