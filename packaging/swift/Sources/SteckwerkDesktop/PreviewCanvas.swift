import SwiftUI

struct PreviewCanvas: View {
    let svgContent: String

    @State var scale: CGFloat = 1.0
    @State var offset: CGSize = .zero

    var body: some View {
        Canvas { context in
            drawSVGPlaceholder(context: &context)
        }
        .scaleEffect(scale)
        .offset(offset)
        .gesture(
            MagnificationGesture()
                .onChanged { value in
                    scale = value
                }
                .simultaneously(with:
                    DragGesture()
                        .onChanged { value in
                            offset = value.translation
                        }
                )
        )
        .background(Color.white)
    }

    private func drawSVGPlaceholder(context: inout GraphicsContext) {
        let width = 210.0 * 2.8
        let height = 297.0 * 2.8

        var path = Path(roundedRect: .init(x: 0, y: 0, width: width, height: height), cornerRadius: 4)
        context.fill(path, with: .color(.white))
        context.stroke(path, with: .color(.black), lineWidth: 2)

        let centerX = width / 2
        let centerY = height / 2

        context.draw(Text("Vorschau (SVG)").font(.system(size: 12)), at: .init(x: centerX, y: centerY))
    }
}

#Preview {
    PreviewCanvas(svgContent: "<svg></svg>")
        .frame(height: 400)
}
