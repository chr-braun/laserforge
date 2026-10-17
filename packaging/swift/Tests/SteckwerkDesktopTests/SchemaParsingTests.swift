import XCTest

class SchemaParsingTests: XCTestCase {

    func testFullSchemaStructure() throws {
        let json = """
        {
            "models": [
                {
                    "key": "wichtelhaus",
                    "label": "Wichtelhaus",
                    "desc": "Kleines Haus aus Holz",
                    "group": "Häuser",
                    "params": [
                        {
                            "key": "hoehe",
                            "label": "Höhe",
                            "type": "num",
                            "default": 150,
                            "options": null,
                            "min": 50,
                            "max": 300,
                            "step": 5,
                            "unit": "mm",
                            "help": "Gesamthöhe des Hauses",
                            "section": "Abmessungen"
                        },
                        {
                            "key": "material",
                            "label": "Material",
                            "type": "select",
                            "default": "oak",
                            "options": [
                                {"label": "Eiche", "value": "oak"},
                                {"label": "Buche", "value": "beech"}
                            ],
                            "min": null,
                            "max": null,
                            "step": null,
                            "unit": null,
                            "help": "Holzart",
                            "section": "Material"
                        }
                    ]
                }
            ],
            "config": {
                "kerf": 0.3,
                "material_thickness": 3.0,
                "scale": 1.0
            },
            "motive": [
                {
                    "key": "herz",
                    "label": "Herz",
                    "thumb": "data:image/png;base64,..."
                }
            ],
            "pakete": [
                {
                    "channel": "main",
                    "packages": ["paket1", "paket2"]
                }
            ]
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let schema = try decoder.decode(Schema.self, from: data)

        XCTAssertEqual(schema.models.count, 1)
        XCTAssertEqual(schema.models[0].params.count, 2)
        XCTAssertEqual(schema.motive.count, 1)
        XCTAssertEqual(schema.pakete[0].packages.count, 2)
    }

    func testParameterTypes() throws {
        let paramTypes = ["num", "int", "select", "text", "flag", "motiv", "motive"]

        for type in paramTypes {
            let json = """
            {
                "key": "test",
                "label": "Test",
                "type": "\(type)",
                "default": 0,
                "options": null,
                "min": null,
                "max": null,
                "step": null,
                "unit": null,
                "help": null,
                "section": null
            }
            """

            let data = json.data(using: .utf8)!
            let decoder = JSONDecoder()
            let param = try decoder.decode(Schema.Parameter.self, from: data)

            XCTAssertEqual(param.type, type)
        }
    }

    func testConfigDefaults() throws {
        let json = """
        {
            "models": [],
            "config": {
                "kerf": null,
                "material_thickness": null,
                "scale": null
            },
            "motive": [],
            "pakete": []
        }
        """

        let data = json.data(using: .utf8)!
        let decoder = JSONDecoder()
        let schema = try decoder.decode(Schema.self, from: data)

        XCTAssertNil(schema.config.kerf)
        XCTAssertNil(schema.config.material_thickness)
    }
}
