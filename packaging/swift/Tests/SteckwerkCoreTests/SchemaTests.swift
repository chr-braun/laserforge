import Foundation
import XCTest
@testable import SteckwerkCore

final class SchemaTests: XCTestCase {
    func testDecodesModelsKeyedByID() throws {
        let schema = try Fixture.schema()
        XCTAssertEqual(Set(schema.models.keys), ["wichtelhaus", "motiv_aufsteller", "motiv_silhouette", "ornament"])
        let haus = try XCTUnwrap(schema.models["wichtelhaus"])
        XCTAssertEqual(haus.label, "Wichtelhaus")
        XCTAssertEqual(haus.group, "Häuser")
        XCTAssertFalse(haus.params.isEmpty)
    }

    func testParamKindsAndFields() throws {
        let params = try XCTUnwrap(Fixture.schema().models["wichtelhaus"]).params
        let width = try XCTUnwrap(params.first { $0.key == "width" })
        XCTAssertEqual(width.kind, .number)
        XCTAssertEqual(width.unit, "mm")
        XCTAssertEqual(width.min, 40)
        XCTAssertEqual(width.max, 300)
        XCTAssertEqual(width.defaultValue.doubleValue, 80)

        let door = try XCTUnwrap(params.first { $0.key == "door" })
        XCTAssertEqual(door.kind, .select)
        XCTAssertTrue(door.options.contains(ParamOption(value: .string("arched"), label: "Rundbogen")))

        let light = try XCTUnwrap(params.first { $0.key == "light" })
        XCTAssertEqual(light.kind, .bool)
        XCTAssertEqual(light.defaultValue, .bool(true))

        let giebel = try XCTUnwrap(params.first { $0.key == "giebel_text" })
        XCTAssertEqual(giebel.kind, .text)
        XCTAssertEqual(giebel.maxlength, 24)
        XCTAssertEqual(giebel.when["giebel"], [.string("text")])
    }

    func testAllEngineTypesAreKnown() throws {
        let schema = try Fixture.schema()
        for (_, model) in schema.models {
            for p in model.params {
                XCTAssertNotEqual(p.kind, .unknown, "\(p.key) hat unbekannten Typ \(p.type)")
            }
        }
        XCTAssertTrue(schema.config.allSatisfy { $0.kind != .unknown })
    }

    func testMotiveParamTypes() throws {
        let schema = try Fixture.schema()
        let motive = try XCTUnwrap(schema.models["motiv_aufsteller"]?.params.first { $0.key == "motive" })
        XCTAssertEqual(motive.kind, .motive)
        XCTAssertEqual(motive.max, 12)
        XCTAssertFalse(motive.arten.isEmpty)
        XCTAssertEqual(motive.defaultValue.arrayValue?.count, 1)

        let motiv = try XCTUnwrap(schema.models["motiv_silhouette"]?.params.first { $0.key == "motiv" })
        XCTAssertEqual(motiv.kind, .motiv)
        XCTAssertEqual(motiv.defaultValue, .string("katze"))
    }

    func testWhenWithBoolean() throws {
        let rand = try XCTUnwrap(Fixture.schema().models["ornament"]?.params.first { $0.key == "rand_stil" })
        XCTAssertEqual(rand.when["rand"], [.bool(true)])
    }

    func testConfigIsMaterialParameterList() throws {
        let keys = try Fixture.schema().config.map(\.key)
        XCTAssertEqual(keys, ["thickness", "kerf", "scale", "openings", "sheet_width", "sheet_height", "cut_color", "engrave_color"])
    }

    func testSidebarGroupsFollowEngineOrder() throws {
        let schema = try Fixture.schema()
        let groups = schema.sidebarGroups
        let order = groups.map { schema.groups.firstIndex(of: $0.id) ?? Int.max }
        XCTAssertEqual(order, order.sorted())
        XCTAssertEqual(groups.first?.id, "Häuser")
        let all = groups.flatMap(\.models).map(\.id)
        XCTAssertEqual(Set(all).count, 4)
        for group in groups {
            let labels = group.models.map { $0.info.label.lowercased() }
            XCTAssertEqual(labels, labels.sorted())
        }
    }

    func testMotivLibraryAndPakete() throws {
        let schema = try Fixture.schema()
        let stern = try XCTUnwrap(schema.motiv(id: "stern"))
        XCTAssertFalse(stern.flaechen.isEmpty)
        XCTAssertGreaterThan(stern.flaechen[0].aussen.count, 2)
        XCTAssertEqual(schema.pakete.first?.id, "tuerschild")
        XCTAssertEqual(schema.pakete.first?.modelle, ["tuerschild"])
    }

    func testKISettingsNeverContainKeys() throws {
        let bilder = try XCTUnwrap(Fixture.schema().assistent?.bilder)
        XCTAssertFalse(bilder.stile.isEmpty)
        let raw = try JSONDecoder().decode([String: JSONValue].self, from: Fixture.data("schema"))
        let bilderRaw = try XCTUnwrap(raw["assistent"]?.objectValue?["bilder"]?.objectValue)
        XCTAssertNil(bilderRaw["key"], "Die Bild-Einstellungen dürfen nie einen Schlüssel enthalten")
        XCTAssertNil(bilderRaw["chatgpt_key"])
    }

    func testMultilineTextHasRows() throws {
        let json = #"{"key": "liste", "type": "text", "default": "", "rows": 6}"#
        let p = try JSONDecoder().decode(Param.self, from: Data(json.utf8))
        XCTAssertEqual(p.kind, .text)
        XCTAssertEqual(p.rows, 6)
        let single = try XCTUnwrap(Fixture.schema().models["wichtelhaus"]?.params.first { $0.key == "giebel_text" })
        XCTAssertNil(single.rows)
    }

    func testToleratesMissingOptionalFields() throws {
        let json = #"{"models": {"x": {"label": "X", "params": [{"key": "a", "type": "flag", "default": false}]}}}"#
        let schema = try JSONDecoder().decode(Schema.self, from: Data(json.utf8))
        let p = try XCTUnwrap(schema.models["x"]?.params.first)
        XCTAssertEqual(p.kind, .bool)
        XCTAssertEqual(p.label, "a")
        XCTAssertTrue(schema.config.isEmpty)
        XCTAssertEqual(schema.sidebarGroups.first?.models.first?.id, "x")
    }
}
