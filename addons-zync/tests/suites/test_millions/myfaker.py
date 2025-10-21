import uuid


class myfaker:
    def fake_data(self, count):
        from faker import Faker

        fake = Faker()
        res = []
        for i in range(int(count)):
            addr = fake.address()
            res.append(
                {
                    "name": fake.name(),
                    "street": addr.split("\n")[0],
                    "street2": str(uuid.uuid4()),
                    "city": addr.split("\n")[1],
                }
            )
        return res

    def make_csv_file(self):
        import csv

        records = self.fake_data(50000)

        # Define the filename
        filename = "output.csv"

        # Field names (column headers)
        fields = ["name", "street", "city", "street2"]

        # Writing to a CSV file
        with open(filename, mode="w", newline="") as csvfile:
            # Create a writer object
            writer = csv.DictWriter(csvfile, fieldnames=fields)

            # Write the headers
            writer.writeheader()

            # Write the data rows
            for i, record in enumerate(records, 1):
                writer.writerow(record)
                if i % 100 == 0:
                    print(f"{i} records written to '{filename}'")

        print(f"CSV file '{filename}' created successfully.")
