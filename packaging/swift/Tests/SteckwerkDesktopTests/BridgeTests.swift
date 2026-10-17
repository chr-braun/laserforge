import XCTest

class BridgeTests: XCTestCase {

    func testAnyCodableInt() throws {
        let value = AnyCodable(42)
        let encoded = try JSONEncoder().encode(value)
        let decoded = try JSONDecoder().decode(AnyCodable.self, from: encoded)

        if let intVal = decoded.value as? Int {
            XCTAssertEqual(intVal, 42)
        } else {
            XCTFail("AnyCodable should decode to Int")
        }
    }

    func testAnyCodableString() throws {
        let value = AnyCodable("test")
        let encoded = try JSONEncoder().encode(value)
        let decoded = try JSONDecoder().decode(AnyCodable.self, from: encoded)

        if let stringVal = decoded.value as? String {
            XCTAssertEqual(stringVal, "test")
        } else {
            XCTFail("AnyCodable should decode to String")
        }
    }

    func testAnyCodableArray() throws {
        let value = AnyCodable([1, 2, 3])
        let encoded = try JSONEncoder().encode(value)
        let decoded = try JSONDecoder().decode(AnyCodable.self, from: encoded)

        if let arrayVal = decoded.value as? [Any] {
            XCTAssertEqual(arrayVal.count, 3)
        } else {
            XCTFail("AnyCodable should decode to Array")
        }
    }

    func testAnyCodableDictionary() throws {
        let value = AnyCodable(["key": "value"])
        let encoded = try JSONEncoder().encode(value)
        let decoded = try JSONDecoder().decode(AnyCodable.self, from: encoded)

        if let dictVal = decoded.value as? [String: Any] {
            XCTAssertEqual(dictVal.count, 1)
        } else {
            XCTFail("AnyCodable should decode to Dictionary")
        }
    }

    func testGenerateResponseDecoding() throws {
        let json = """
        {
            "status": "ok",
            "fehler": null,
            "warnungen": null,
            "data": {
                "svg": "<svg></svg>",
                "geometrie": {
                    "blattbreite": 600,
                    "blatthoehe": 800,
                    "schnittbreite": 100,
                    "schnitthoehe": 150
                },
                "teile": []
            }
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let response = try decoder.decode(GenerateResponse.self, from: data)

        XCTAssertEqual(response.status, "ok")
        XCTAssertNotNil(response.data?.svg)
    }
}
