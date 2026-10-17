import Foundation
import XCTest
@testable import SteckwerkCore

final class SheetGeometryTests: XCTestCase {
    func testParsesEngineSheet() throws {
        let sheet = try XCTUnwrap(Fixture.generate().assemblies.first?.sheets.first)
        let geo = SheetGeometry.parse(svg: sheet.svg)
        XCTAssertEqual(geo.width, 400)
        XCTAssertEqual(geo.height, 300)
        XCTAssertGreaterThan(geo.cutCount, 0)
        XCTAssertGreaterThan(geo.engraveCount, 0)
        for line in geo.lines {
            XCTAssertGreaterThanOrEqual(line.points.count, 2)
            for p in line.points {
                XCTAssertTrue((0...geo.width).contains(p.x) && (0...geo.height).contains(p.y), "Punkt außerhalb des Blatts: \(p)")
            }
        }
    }

    func testSubpathCommands() {
        let paths = SheetGeometry.subpaths("M1,2 L3,4 L5,6 Z M7 8 l1 1 h2 v-3 z M0 0 1e1 0 1.5e+1,-2E-1")
        XCTAssertEqual(paths.count, 3)
        XCTAssertEqual(paths[0].points, [Point(x: 1, y: 2), Point(x: 3, y: 4), Point(x: 5, y: 6)])
        XCTAssertTrue(paths[0].closed)
        XCTAssertEqual(paths[1].points, [Point(x: 7, y: 8), Point(x: 8, y: 9), Point(x: 10, y: 9), Point(x: 10, y: 6)])
        XCTAssertTrue(paths[1].closed)
        XCTAssertEqual(paths[2].points, [Point(x: 0, y: 0), Point(x: 10, y: 0), Point(x: 15, y: -0.2)])
        XCTAssertFalse(paths[2].closed)
    }

    func testClassifiesByColorWithoutLayers() {
        let svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm">
          <path d="M0,0 L10,10" stroke="#ff0000"/>
          <g stroke="#00AA00"><path d="M1,1 L2,2"/></g>
        </svg>
        """
        let geo = SheetGeometry.parse(svg: svg, engraveColor: "#00aa00")
        XCTAssertEqual(geo.width, 100)
        XCTAssertEqual(geo.height, 50)
        XCTAssertEqual(geo.lines.map(\.kind), [.cut, .engrave])
    }

    func testBrokenSVGDoesNotCrash() {
        let geo = SheetGeometry.parse(svg: "<svg><path d=\"M1")
        XCTAssertTrue(geo.lines.isEmpty)
    }
}

final class ReportTests: XCTestCase {
    func testStatusTextShowsZeroErrors() throws {
        let result = try Fixture.generate()
        XCTAssertTrue(result.canExport)
        XCTAssertEqual(result.errorCount, 0)
        let text = ReportFormatter.statusText(result)
        XCTAssertTrue(text.hasPrefix("0 FEHLER"), text)
        XCTAssertTrue(text.contains("CUT-READY"))
    }

    func testReportLinesAreClassified() throws {
        let assembly = try XCTUnwrap(Fixture.generate().assemblies.first)
        let lines = ReportFormatter.lines(assembly.report)
        XCTAssertFalse(lines.isEmpty)
        XCTAssertTrue(lines.contains { $0.status == .ok })
        XCTAssertFalse(lines.contains { $0.status == .error })
        let mixed = ReportFormatter.lines("OK      a\nFEHLER  b\nWARNUNG c\nfrei")
        XCTAssertEqual(mixed.map(\.status), [.ok, .error, .warning, .info])
    }

    func testExportFilesMirrorEngineLayout() throws {
        let result = try Fixture.generate()
        let files = ReportFormatter.exportFiles(result)
        let assembly = try XCTUnwrap(result.assemblies.first)
        XCTAssertEqual(files.count, assembly.sheets.count + 1)
        XCTAssertTrue(files.contains { $0.relativePath == "wichtelhaus/pruefbericht.txt" })
        XCTAssertTrue(files.contains { $0.relativePath.hasSuffix(".svg") && $0.contents.contains("<svg") })
        let bericht = try XCTUnwrap(files.first { $0.relativePath.hasSuffix("pruefbericht.txt") }).contents
        XCTAssertTrue(bericht.contains("0 FEHLER"))
        XCTAssertTrue(bericht.contains("Montagehinweise:"))
    }

    func testNoExportWhenValidationFails() throws {
        let failed = try JSONDecoder().decode(GenerateResponse.self, from: Fixture.data("generate_unknown_model"))
        XCTAssertTrue(ReportFormatter.exportFiles(failed).isEmpty)
    }

    func testSafeNamesStayInsideTarget() {
        XCTAssertEqual(ReportFormatter.safeName("../../etc/passwd", fallback: "x"), "passwd")
        XCTAssertEqual(ReportFormatter.safeName("..", fallback: "x"), "x")
        XCTAssertEqual(ReportFormatter.safeName("", fallback: "x"), "x")
        XCTAssertEqual(ReportFormatter.safeName("a\\b.svg", fallback: "x"), "b.svg")
    }

    func testWriteCreatesFiles() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("steckwerk-export-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: dir) }
        let written = try ReportFormatter.write(ReportFormatter.exportFiles(Fixture.generate()), to: dir)
        XCTAssertFalse(written.isEmpty)
        for url in written {
            XCTAssertTrue(FileManager.default.fileExists(atPath: url.path))
            XCTAssertTrue(url.path.hasPrefix(dir.path))
        }
    }
}
