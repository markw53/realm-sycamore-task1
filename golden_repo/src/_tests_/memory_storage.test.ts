import { MemoryStorage } from "../storage/memory";

describe("MemoryStorage", () => {
  let store: MemoryStorage;

  beforeEach(() => {
    store = new MemoryStorage();
  });

  test("save and load roundtrip", async () => {
    await store.save("key1", { data: "test" });
    const loaded = await store.load("key1");
    expect(loaded).toEqual({ data: "test" });
  });

  test("load returns null for missing key", async () => {
    expect(await store.load("missing")).toBeNull();
  });

  test("delete existing key returns true", async () => {
    await store.save("k", { x: 1 });
    expect(await store.delete("k")).toBe(true);
    expect(await store.load("k")).toBeNull();
  });

  test("delete missing key returns false", async () => {
    expect(await store.delete("nope")).toBe(false);
  });

  test("exists returns correct boolean", async () => {
    await store.save("e", {});
    expect(await store.exists("e")).toBe(true);
    expect(await store.exists("nope")).toBe(false);
  });

  test("listKeys with prefix filtering", async () => {
    await store.save("user:1", {});
    await store.save("user:2", {});
    await store.save("job:1", {});
    expect(await store.listKeys("user:")).toEqual(["user:1", "user:2"]);
  });

  test("listKeys returns sorted results", async () => {
    await store.save("c", {});
    await store.save("a", {});
    await store.save("b", {});
    expect(await store.listKeys()).toEqual(["a", "b", "c"]);
  });

  test("save makes a copy — mutations don't affect stored data", async () => {
    const original = { mutable: "yes" };
    await store.save("copy-test", original);
    original.mutable = "mutated";
    const loaded = await store.load("copy-test");
    expect(loaded!.mutable).toBe("yes");
  });

  test("load returns a copy — mutations don't affect stored data", async () => {
    await store.save("copy-test2", { value: "original" });
    const loaded = await store.load("copy-test2");
    loaded!.value = "mutated";
    const reloaded = await store.load("copy-test2");
    expect(reloaded!.value).toBe("original");
  });

  test("overwrite existing key", async () => {
    await store.save("ow", { v: 1 });
    await store.save("ow", { v: 2 });
    expect(await store.load("ow")).toEqual({ v: 2 });
  });
});