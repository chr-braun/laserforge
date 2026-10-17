import SteckwerkCore
import SwiftUI

/// Native Vorschau eines Blattplans: Schnitt schwarz, Gravur blau, Blattrahmen; Zoom (Pinch/Scroll) und Verschieben.
@MainActor
struct PreviewCanvas: View {
    let geometry: SheetGeometry
    let checked: Bool

    @State var zoom: CGFloat = 1
    @State var committedZoom: CGFloat = 1
    @State var offset: CGSize = .zero
    @State var committedOffset: CGSize = .zero

    var body: some View {
        ZStack(alignment: .topLeading) {
            Canvas { context, size in
                draw(in: &context, size: size)
            }
            .background(Theme.card)
            .clipShape(RoundedRectangle(cornerRadius: Theme.cornerRadius))
            .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.1)))
            .contentShape(Rectangle())
            .gesture(
                MagnificationGesture()
                    .onChanged { zoom = clampZoom(committedZoom * $0) }
                    .onEnded { _ in committedZoom = zoom }
                    .simultaneously(with: DragGesture()
                        .onChanged { drag in
                            offset = CGSize(width: committedOffset.width + drag.translation.width,
                                            height: committedOffset.height + drag.translation.height)
                        }
                        .onEnded { _ in committedOffset = offset })
            )
            .onTapGesture(count: 2) { reset() }

            HStack(spacing: 8) {
                legend(color: Theme.cut, text: "Schnitt \(geometry.cutCount)")
                legend(color: Theme.engrave, text: "Gravur \(geometry.engraveCount)")
                if !checked {
                    Text("Vorschau – nicht geprüft")
                        .foregroundStyle(Theme.error)
                }
                Text("\(Int(geometry.width)) × \(Int(geometry.height)) mm")
                    .foregroundStyle(.secondary)
            }
            .font(.caption)
            .padding(6)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 6))
            .padding(8)

            VStack {
                Spacer()
                HStack {
                    Spacer()
                    HStack(spacing: 4) {
                        Button { setZoom(zoom / 1.25) } label: { Image(systemName: "minus.magnifyingglass") }
                        Button { reset() } label: { Text("\(Int((zoom * 100).rounded())) %").monospacedDigit() }
                        Button { setZoom(zoom * 1.25) } label: { Image(systemName: "plus.magnifyingglass") }
                    }
                    .buttonStyle(.borderless)
                    .padding(6)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 6))
                    .padding(8)
                }
            }
        }
    }

    private func draw(in context: inout GraphicsContext, size: CGSize) {
        guard geometry.width > 0, geometry.height > 0 else { return }
        let margin: CGFloat = 16
        let fit = min((size.width - 2 * margin) / geometry.width, (size.height - 2 * margin) / geometry.height)
        let scale = max(fit, 0.01) * zoom
        let origin = CGPoint(x: (size.width - geometry.width * scale) / 2 + offset.width,
                             y: (size.height - geometry.height * scale) / 2 + offset.height)
        func map(_ p: SteckwerkCore.Point) -> CGPoint {
            CGPoint(x: origin.x + p.x * scale, y: origin.y + p.y * scale)
        }

        let frame = CGRect(x: origin.x, y: origin.y, width: geometry.width * scale, height: geometry.height * scale)
        context.fill(Path(frame), with: .color(Theme.accent.opacity(0.05)))
        context.stroke(Path(frame), with: .color(Theme.accent.opacity(0.6)), style: StrokeStyle(lineWidth: 1, dash: [4, 3]))

        var cut = Path()
        var engrave = Path()
        for line in geometry.lines {
            guard let first = line.points.first else { continue }
            var path = Path()
            path.move(to: map(first))
            for p in line.points.dropFirst() { path.addLine(to: map(p)) }
            if line.closed { path.closeSubpath() }
            if line.kind == .engrave {
                engrave.addPath(path)
            } else {
                cut.addPath(path)
            }
        }
        context.stroke(engrave, with: .color(Theme.engrave), lineWidth: 0.8)
        context.stroke(cut, with: .color(Theme.cut), lineWidth: 1)
    }

    private func legend(color: Color, text: String) -> some View {
        HStack(spacing: 4) {
            RoundedRectangle(cornerRadius: 1).fill(color).frame(width: 14, height: 3)
            Text(text)
        }
    }

    private func clampZoom(_ value: CGFloat) -> CGFloat {
        min(max(value, 0.2), 20)
    }

    private func setZoom(_ value: CGFloat) {
        zoom = clampZoom(value)
        committedZoom = zoom
    }

    private func reset() {
        zoom = 1
        committedZoom = 1
        offset = .zero
        committedOffset = .zero
    }
}
