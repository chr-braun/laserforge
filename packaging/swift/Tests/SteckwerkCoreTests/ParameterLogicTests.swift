import Foundation
import XCTest
@testable import SteckwerkCore

final class ParameterLogicTests: XCTestCase {
    private func params(_ model: String) throws -> [Param] {
        try XCTUnwrap(Fixture.schema().models[model]).params
    }

    func testDefaults() throws {
        let values = ParameterLogic.defaults(for: try params("wichtelhaus"))
        XCTAssertEqual(values["width"]?.doubleValue, 80)
        XCTAssertEqual(values["door"], .string("arched"))
        XCTAssertEqual(values["light"], .bool(true))
    }

    func testVisibilityFollowsWhen() throws {
        let ps = try params("wichtelhaus")
        let giebelText = try XCTUnwrap(ps.first { $0.key == "giebel_text" })
        var values = ParameterLogic.defaults(for: ps)
        values["giebel"] = .string("ohne")
        XCTAssertFalse(ParameterLogic.isVisible(giebelText, values: values))
        values["giebel"] = .string("text")
        XCTAssertTrue(ParameterLogic.isVisible(giebelText, values: values))

        let rand = try XCTUnwrap(try params("ornament").first { $0.key == "rand_stil" })
        XCTAssertFalse(ParameterLogic.isVisible(rand, values: ["rand": .bool(false)]))
        XCTAssertTrue(ParameterLogic.isVisible(rand, values: ["rand": .bool(true)]))
        XCTAssertFalse(ParameterLogic.isVisible(rand, values: [:]))
    }

    func testSectionsKeepOrderOfFirstAppearance() throws {
        let ps = try params("wichtelhaus")
        let sections = ParameterLogic.sections(ps)
        XCTAssertEqual(sections.flatMap(\.params).map(\.key), ps.map(\.key).filter { k in
            sections.flatMap(\.params).contains { $0.key == k }
        })
        XCTAssertEqual(sections.reduce(0) { $0 + $1.params.count }, ps.count)
        XCTAssertNil(sections.first?.title)
        XCTAssertEqual(Set(sections.map(\.id)).count, sections.count)
    }

    func testCoerceNumbers() throws {
        let width = try XCTUnwrap(try params("wichtelhaus").first { $0.key == "width" })
        XCTAssertEqual(ParameterLogic.coerce(.double(1000), for: width), .double(300))
        XCTAssertEqual(ParameterLogic.coerce(.int(10), for: width), .double(40))
        XCTAssertEqual(ParameterLogic.coerce(.string("95,5"), for: width), .double(95.5))
        XCTAssertEqual(ParameterLogic.coerce(.string("abc"), for: width), width.defaultValue)

        let windows = try XCTUnwrap(try params("wichtelhaus").first { $0.key == "front_windows" })
        XCTAssertEqual(ParameterLogic.coerce(.double(2.6), for: windows), .int(3))
        XCTAssertEqual(ParameterLogic.coerce(.int(99), for: windows), .int(4))
    }

    func testCoerceSelectTextAndMotive() throws {
        let ps = try params("wichtelhaus")
        let door = try XCTUnwrap(ps.first { $0.key == "door" })
        XCTAssertEqual(ParameterLogic.coerce(.string("gibtsnicht"), for: door), door.defaultValue)
        XCTAssertEqual(ParameterLogic.coerce(.string("rect"), for: door), .string("rect"))

        let text = try XCTUnwrap(ps.first { $0.key == "giebel_text" })
        let long = String(repeating: "x", count: 40)
        XCTAssertEqual(ParameterLogic.coerce(.string(long), for: text).stringValue?.count, 24)

        let motive = try XCTUnwrap(try params("motiv_aufsteller").first { $0.key == "motive" })
        let many = JSONValue.array(Array(repeating: motive.defaultValue.arrayValue![0], count: 20))
        XCTAssertEqual(ParameterLogic.coerce(many, for: motive).arrayValue?.count, 12)
    }

    func testRequestValuesOnlyKnownKeys() throws {
        let ps = try params("wichtelhaus")
        let out = ParameterLogic.requestValues(ps, values: ["width": .double(120), "fremd": .string("x")])
        XCTAssertEqual(Set(out.keys), Set(ps.map(\.key)))
        XCTAssertEqual(out["width"], .double(120))
        XCTAssertNil(out["fremd"])
    }

    func testApplyReportsChangedKeys() throws {
        let ps = try params("wichtelhaus")
        var values = ParameterLogic.defaults(for: ps)
        let changed = ParameterLogic.apply(["width": .int(80), "depth": .int(100), "light": .bool(false), "x": .int(1)],
                                           to: &values, params: ps)
        XCTAssertEqual(Set(changed), ["depth", "light"])
        XCTAssertEqual(values["depth"], .double(100))
    }

    func testDecimals() {
        XCTAssertEqual(ParameterLogic.decimals(for: Param(key: "a", label: "a", type: "number", defaultValue: .int(1), step: 0.05)), 2)
        XCTAssertEqual(ParameterLogic.decimals(for: Param(key: "a", label: "a", type: "number", defaultValue: .int(1), step: 1)), 0)
        XCTAssertEqual(ParameterLogic.decimals(for: Param(key: "a", label: "a", type: "int", defaultValue: .int(1))), 0)
    }

    func testMotivPlacementRoundTripKeepsUnknownFields() {
        let raw: JSONValue = .object(["id": .string("stern"), "x": .int(1), "y": .double(-3.5), "groesse": .int(30),
                                      "drehung": .double(0), "spiegeln": .bool(false), "art": .string("schnitt"),
                                      "zukunft": .string("bleibt")])
        var p = MotivPlacement(json: raw)
        XCTAssertEqual(p.motivID, "stern")
        XCTAssertEqual(p.y, -3.5)
        p.groesse = 45
        let back = p.json.objectValue!
        XCTAssertEqual(back["groesse"], .double(45))
        XCTAssertEqual(back["zukunft"], .string("bleibt"))
        XCTAssertEqual(MotivPlacement.list(MotivPlacement.json([p])).first, p)
    }
}
