import Foundation
import XCTest
@testable import SteckwerkCore

final class JSONValueTests: XCTestCase {
    func testDecodesAllKinds() throws {
        let json = #"{"a": null, "b": true, "c": 3, "d": 2.5, "e": "x", "f": [1, "y"], "g": {"h": false}}"#
        let v = try JSONDecoder().decode([String: JSONValue].self, from: Data(json.utf8))
        XCTAssertEqual(v["a"], .null)
        XCTAssertEqual(v["b"], .bool(true))
        XCTAssertEqual(v["c"]?.doubleValue, 3)
        XCTAssertEqual(v["d"], .double(2.5))
        XCTAssertEqual(v["e"], .string("x"))
        XCTAssertEqual(v["f"]?.arrayValue?.count, 2)
        XCTAssertEqual(v["g"]?.objectValue?["h"], .bool(false))
    }

    func testBooleansStayBooleans() throws {
        let v = try JSONDecoder().decode([JSONValue].self, from: Data("[true, false, 1, 0]".utf8))
        XCTAssertEqual(v[0], .bool(true))
        XCTAssertEqual(v[1], .bool(false))
        XCTAssertNil(v[2].boolValue)
        XCTAssertEqual(v[3].doubleValue, 0)
    }

    func testRoundTrip() throws {
        let value: JSONValue = .object(["n": .double(1.25), "i": .int(7), "s": .string("ä"), "l": .array([.bool(true), .null])])
        let data = try JSONEncoder().encode(value)
        XCTAssertEqual(try JSONDecoder().decode(JSONValue.self, from: data), value)
    }

    func testLooseEqualityForNumbers() {
        XCTAssertTrue(JSONValue.int(3).looselyEquals(.double(3.0)))
        XCTAssertFalse(JSONValue.int(3).looselyEquals(.string("3")))
        XCTAssertTrue(JSONValue.string("a").looselyEquals(.string("a")))
    }

    func testDisplayText() {
        XCTAssertEqual(JSONValue.double(80).displayText, "80")
        XCTAssertEqual(JSONValue.double(0.15).displayText, "0.15")
        XCTAssertEqual(JSONValue.double(1.0 / 3).displayText, "0.3333")
        XCTAssertEqual(JSONValue.int(-2).displayText, "-2")
        XCTAssertEqual(JSONValue.null.displayText, "")
    }
}
