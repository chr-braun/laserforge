import SwiftUI

struct ParameterForm: View {
    let model: ModelSchema
    @EnvironmentObject var engineManager: EngineManager
    @State private var paramValues: [String: AnyCodable] = [:]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(model.label)
                    .font(.title2)
                    .fontWeight(.bold)

                Text(model.desc)
                    .font(.body)
                    .foregroundColor(.secondary)

                Divider()

                let groupedParams = Dictionary(grouping: model.params) { $0.section ?? "Allgemein" }

                ForEach(Array(groupedParams.keys).sorted(), id: \.self) { section in
                    Section(header: Text(section).font(.headline)) {
                        VStack(alignment: .leading, spacing: 12) {
                            ForEach(groupedParams[section] ?? [], id: \.key) { param in
                                ParamControl(param: param, value: .constant(paramValues[param.key] ?? param.default))
                            }
                        }
                    }
                }

                Spacer()
            }
            .padding()
        }
        .onAppear {
            for param in model.params {
                paramValues[param.key] = param.default
            }
        }
    }
}

struct ParamControl: View {
    let param: ParamSchema
    @Binding var value: AnyCodable

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(param.label)
                    .fontWeight(.medium)

                if let help = param.help {
                    Image(systemName: "questionmark.circle")
                        .foregroundColor(.secondary)
                        .help(help)
                }

                Spacer()
            }

            switch param.type {
            case "num", "int":
                if let min = param.min, let max = param.max, let step = param.step {
                    HStack {
                        Slider(
                            value: .constant(doubleValue),
                            in: min...max,
                            step: step
                        )

                        Text(String(format: "%.1f", doubleValue))
                            .font(.monospaced(.body)())
                            .frame(width: 50)

                        if let unit = param.unit {
                            Text(unit)
                                .foregroundColor(.secondary)
                        }
                    }
                } else {
                    TextField("Wert", text: .constant(String(describing: value.value)))
                        .textFieldStyle(.roundedBorder)
                }

            case "select":
                if let options = param.options {
                    Picker(param.label, selection: .constant(stringValue)) {
                        ForEach(options, id: \.self) { option in
                            Text(option).tag(option)
                        }
                    }
                    .pickerStyle(.segmented)
                }

            case "flag":
                Toggle(isOn: .constant(boolValue)) {
                    Text(param.label)
                }

            case "text":
                TextEditor(text: .constant(stringValue))
                    .frame(minHeight: 80)
                    .border(Color.gray, width: 0.5)
                    .cornerRadius(4)

            case "motiv", "motive":
                Text("Motiv-Auswahl (TODO)")
                    .foregroundColor(.secondary)

            default:
                Text("Unbekannter Parametertyp: \(param.type)")
                    .foregroundColor(.red)
            }
        }
    }

    private var doubleValue: Double {
        if let d = value.value as? Double {
            return d
        } else if let i = value.value as? Int {
            return Double(i)
        }
        return 0
    }

    private var stringValue: String {
        if let s = value.value as? String {
            return s
        }
        return String(describing: value.value)
    }

    private var boolValue: Bool {
        if let b = value.value as? Bool {
            return b
        }
        return false
    }
}

#Preview {
    VStack {
        ParamControl(
            param: ParamSchema(
                type: "int",
                key: "test_param",
                label: "Test Parameter",
                default: AnyCodable(10),
                options: nil,
                min: 0,
                max: 100,
                step: 1,
                unit: "mm",
                help: "Ein Testparameter",
                section: "Test"
            ),
            value: .constant(AnyCodable(10))
        )
        .padding()
    }
}
