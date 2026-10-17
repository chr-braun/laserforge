import SwiftUI

struct ParameterForm: View {
    let parameters: [Schema.Parameter]
    @Binding var values: [String: AnyCodable]

    private var groupedParams: [String: [Schema.Parameter]] {
        Dictionary(grouping: parameters) { $0.section ?? "Allgemein" }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Theme.spacing16) {
            ForEach(Array(groupedParams.sorted { $0.key < $1.key }), id: \.key) { section, params in
                Section(header: Text(section).font(.headline)) {
                    VStack(spacing: Theme.spacing12) {
                        ForEach(params) { param in
                            ParameterControl(
                                parameter: param,
                                value: Binding(
                                    get: { values[param.key] ?? param.default },
                                    set: { values[param.key] = $0 }
                                )
                            )
                        }
                    }
                    .padding(.vertical, Theme.spacing8)
                }
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(Theme.cornerRadius)
    }
}

struct ParameterControl: View {
    let parameter: Schema.Parameter
    @Binding var value: AnyCodable

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(parameter.label)
                    .font(.body)

                if let help = parameter.help {
                    Image(systemName: "info.circle")
                        .foregroundColor(.gray)
                        .help(help)
                }
            }

            Group {
                switch parameter.type {
                case "num", "int":
                    NumericControl(parameter: parameter, value: $value)

                case "select":
                    PickerControl(parameter: parameter, value: $value)

                case "text":
                    TextControl(value: $value)

                case "flag":
                    Toggle("", isOn: Binding(
                        get: { (value as? AnyCodable)?.asBool ?? false },
                        set: { value = .bool($0) }
                    ))

                case "motiv", "motive":
                    Text("Motiv-Auswahl")
                        .foregroundColor(.secondary)

                default:
                    Text("Unbekannter Typ: \(parameter.type)")
                        .foregroundColor(.red)
                }
            }

            if let help = parameter.help {
                Text(help)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct NumericControl: View {
    let parameter: Schema.Parameter
    @Binding var value: AnyCodable

    var doubleValue: Binding<Double> {
        Binding(
            get: {
                switch value {
                case .double(let d): return d
                case .int(let i): return Double(i)
                default: return parameter.default.asDouble ?? 0
                }
            },
            set: {
                if parameter.type == "int" {
                    value = .int(Int($0))
                } else {
                    value = .double($0)
                }
            }
        )
    }

    var body: some View {
        HStack(spacing: Theme.spacing8) {
            if let min = parameter.min, let max = parameter.max {
                Slider(
                    value: doubleValue,
                    in: min...max,
                    step: parameter.step ?? 0.1
                )
            } else {
                Text("−")
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 2) {
                TextField("", value: doubleValue, format: .number)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 60)

                if let unit = parameter.unit {
                    Text(unit)
                        .foregroundColor(.secondary)
                        .font(.caption)
                }
            }
        }
    }
}

struct PickerControl: View {
    let parameter: Schema.Parameter
    @Binding var value: AnyCodable

    var body: some View {
        Picker(parameter.label, selection: $value) {
            if let options = parameter.options {
                ForEach(options, id: \.value.id) { option in
                    Text(option.label).tag(option.value)
                }
            }
        }
        .pickerStyle(.segmented)
    }
}

struct TextControl: View {
    @Binding var value: AnyCodable

    var stringValue: Binding<String> {
        Binding(
            get: {
                switch value {
                case .string(let s): return s
                default: return ""
                }
            },
            set: { value = .string($0) }
        )
    }

    var body: some View {
        TextEditor(text: stringValue)
            .frame(height: 80)
            .border(Color.gray.opacity(0.3), width: 1)
            .cornerRadius(4)
    }
}

extension AnyCodable {
    var asDouble: Double? {
        switch self {
        case .double(let d): return d
        case .int(let i): return Double(i)
        case .string(let s): return Double(s)
        default: return nil
        }
    }

    var asBool: Bool? {
        switch self {
        case .bool(let b): return b
        default: return nil
        }
    }

    var asString: String? {
        switch self {
        case .string(let s): return s
        default: return nil
        }
    }

    var id: String {
        switch self {
        case .string(let s): return s
        case .int(let i): return "\(i)"
        case .double(let d): return "\(d)"
        case .bool(let b): return "\(b)"
        case .null: return "null"
        }
    }
}

#Preview {
    VStack {
        ParameterForm(
            parameters: [
                .init(
                    id: "durchmesser",
                    label: "Durchmesser",
                    type: "num",
                    key: "durchmesser",
                    default: .double(100),
                    options: nil,
                    min: 10,
                    max: 500,
                    step: 1,
                    unit: "mm",
                    help: "Größe des Objekts",
                    section: "Abmessungen"
                )
            ],
            values: .constant(["durchmesser": .double(100)])
        )
        Spacer()
    }
    .padding()
    .background(Color.warmBg)
}
