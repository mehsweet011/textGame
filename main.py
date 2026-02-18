import json, os, sys, shutil


class WorldGrid:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.home_dir = os.path.dirname(sys.executable)
        else:
            self.home_dir = os.path.dirname(os.path.abspath(__file__))

        self.filename = ""
        self.data = {}
        self.inventory = []
        self.current_pos = [0, 0]
        self.select_world()

    # ... [select_world, create_template, save_world, load_world maintained] ...

    def select_world(self):
        files = [f for f in os.listdir(self.home_dir) if f.lower().endswith('.json')]
        if not files:
            self.filename = os.path.join(self.home_dir, "Default_World.json")
            self.create_template()
        else:
            print("\n--- SELECT ADVENTURE ---")
            for i, f in enumerate(files, 1): print(f"{i}. {f}")
            choice = input("\nSelect # or '0' for New: ").strip()
            if choice == '0':
                name = "".join(x for x in input("World Name: ") if x.isalnum()) or "New_World"
                self.filename = os.path.join(self.home_dir, name + ".json")
                self.create_template()
            elif choice.isdigit() and 1 <= int(choice) <= len(files):
                self.filename = os.path.join(self.home_dir, files[int(choice) - 1])
                self.load_world()
            else:
                sys.exit("Exiting.")

    def create_template(self):
        self.data = {
            "meta": {"width": 10, "height": 10, "start_pos": [0, 0]},
            "locations": {"0,0": "Safe Haven"},
            "descriptions": {"0,0": "The start of your journey. Type 'h' for help."},
            "visited": ["0,0"], "unlocked": [], "items": {}, "master_items": {},
            "item_flavor": {}, "events": {}, "event_descs": {}, "npcs": {}, "npc_descs": {},
            "session_inventory": []
        }
        self.save_world();
        self.load_world()

    def save_world(self):
        try:
            if os.path.exists(self.filename):
                shutil.copy2(self.filename, self.filename + ".bak")
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Save error: {e}")

    def load_world(self):
        with open(self.filename, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        keys = ["items", "master_items", "item_flavor", "events", "event_descs", "npcs", "npc_descs", "unlocked"]
        for k in keys:
            if k not in self.data: self.data[k] = {}
        self.current_pos = list(self.data["meta"].get("start_pos", [0, 0]))
        self.inventory = self.data.get("session_inventory", [])

    def creator_mode(self):
        """Granular CRUD Suite with KeyError Protection."""
        while True:
            try:
                p_str = f"{self.current_pos[0]},{self.current_pos[1]}"
                print(f"\n--- GRANULAR EDITOR ({p_str}) ---")
                print("1. Location | 2. NPCs | 3. Items | 4. Events | 0. Exit")
                choice = input("> ")

                if choice == '0':
                    break

                elif choice == '1':  # LOCATION
                    cur_n = self.data['locations'].get(p_str, "None")
                    cur_d = self.data['descriptions'].get(p_str, "None")
                    print(f"Current: {cur_n}\nDesc: {cur_d}")
                    print("Update: 1. Name | 2. Description")
                    sub = input("> ")
                    if sub == '1':
                        self.data['locations'][p_str] = input("New Name: ")
                    elif sub == '2':
                        self.data['descriptions'][p_str] = input("New Desc: ")

                elif choice == '2':  # NPCs
                    if p_str in self.data['npcs']:
                        npc = self.data['npcs'][p_str]
                        print(
                            f"Editing {npc.get('name', 'Unknown')}: 1. Name | 2. Appearance | 3. Dialogue | 4. Delete")
                        sub = input("> ")
                        if sub == '1':
                            npc['name'] = input("New Name: ")
                        elif sub == '2':
                            self.data['npc_descs'][p_str] = input("New Appearance: ")
                        elif sub == '3':
                            npc['dialogue'] = [input(f"Line {i + 1}: ") for i in range(3)]
                        elif sub == '4':
                            del self.data['npcs'][p_str];
                            del self.data['npc_descs'][p_str]
                    else:
                        print("No NPC here. Create one? (y/n)")
                        if input("> ").lower() == 'y':
                            self.data['npcs'][p_str] = {"name": input("Name: "), "dialogue": [input("Line 1: ")],
                                                        "index": 0}
                            self.data['npc_descs'][p_str] = input("Appearance: ")

                elif choice == '3':  # ITEMS
                    print("1. Place Item Here | 2. Edit Lore | 3. Move Item to Coord")
                    sub = input("> ")
                    if sub == '1':
                        name = input("Item Name: ")
                        self.data['items'].setdefault(p_str, []).append(name)
                        self.data['item_flavor'][name] = input("Lore: ")
                    elif sub == '2':
                        all_items = list(self.data['item_flavor'].keys())
                        for i, itm in enumerate(all_items, 1): print(f"{i}. {itm}")
                        idx = input("Item #: ")
                        if idx.isdigit() and 1 <= int(idx) <= len(all_items):
                            target = all_items[int(idx) - 1]
                            self.data['item_flavor'][target] = input(f"New Lore for {target}: ")
                    elif sub == '3':
                        name = input("Item Name to move: ")
                        dest = input("New Coords (X,Y): ")
                        if ',' in dest:
                            for loc in self.data['items']:
                                if name in self.data['items'][loc]: self.data['items'][loc].remove(name)
                            self.data['items'].setdefault(dest.replace(" ", ""), []).append(name)

                elif choice == '4':  # EVENTS
                    print("Existing Events:")
                    ev_list = list(self.data['events'].keys())
                    for i, coord in enumerate(ev_list, 1):
                        # DEFENSIVE CHECK: Ensure keys exist before printing
                        ev_data = self.data['events'][coord]
                        target = ev_data.get('target', 'UNDEFINED')
                        print(f"{i}. {coord} -> {target}")

                    print("\n1. Create/Update (at current spot) | 2. Edit specific by #")
                    sub = input("> ")

                    target_coord = p_str
                    if sub == '2':
                        idx = input("Event #: ")
                        if idx.isdigit() and 1 <= int(idx) <= len(ev_list):
                            target_coord = ev_list[int(idx) - 1]

                    # Ensure the event entry exists with default keys if missing
                    if target_coord not in self.data['events']:
                        self.data['events'][target_coord] = {"req": "none", "target": [0, 0], "warp": False}

                    ev = self.data['events'][target_coord]
                    print(f"\nEditing Event at {target_coord}:")
                    print(f"1. Required Item: {ev.get('req', 'None')}")
                    print(f"2. Target Coords: {ev.get('target', [0, 0])}")
                    print(f"3. Mode: {'Warp' if ev.get('warp') else 'Unlock'}")
                    print(f"4. Block Message: {self.data['event_descs'].get(target_coord, 'None')}")
                    print("5. Delete Event")

                    field = input("Select field to change > ")
                    if field == '1':
                        ev['req'] = input("New Requirement: ")
                    elif field == '2':
                        tx = int(input("Target X: "))
                        ty = int(input("Target Y: "))
                        ev['target'] = [tx, ty]
                    elif field == '3':
                        ev['warp'] = input("Warp? (y/n): ").lower() == 'y'
                    elif field == '4':
                        self.data['event_descs'][target_coord] = input("New Block Message: ")
                    elif field == '5':
                        del self.data['events'][target_coord]
                        if target_coord in self.data['event_descs']: del self.data['event_descs'][target_coord]

                self.save_world()
            except Exception as e:
                print(f"\n[!] Editor Error: {e}. Returning to main menu.")

    def show_room(self):
        p_str = f"{self.current_pos[0]},{self.current_pos[1]}"
        print(f"\n--- {self.data['locations'].get(p_str, 'THE VOID').upper()} ({p_str}) ---")
        print(self.data['descriptions'].get(p_str, "Nothing here."))
        room_items = self.data['items'].get(p_str, [])
        if room_items: print(f"Ground: {', '.join(room_items)}")
        if p_str in self.data.get('npcs', {}):
            npc = self.data['npcs'][p_str]
            print(f"[NPC] {npc.get('name')}: {self.data['npc_descs'].get(p_str, 'Present.')}")

    def run_command(self, inp):
        inp = inp.strip().lower()
        p_str = f"{self.current_pos[0]},{self.current_pos[1]}"

        if inp in ['h', 'help']:
            print("\nCommands: n, s, e, w | get | talk | use [item] | map | inv | warp | c (Creator) | q")
        elif inp in ['n', 's', 'e', 'w', 'north', 'south', 'east', 'west']:
            m_dirs = {'n': (0, 1), 's': (0, -1), 'e': (1, 0), 'w': (-1, 0), 'north': (0, 1), 'south': (0, -1),
                      'east': (1, 0), 'west': (-1, 0)}
            dx, dy = m_dirs[inp]
            tx, ty = self.current_pos[0] + dx, self.current_pos[1] + dy
            t_str = f"{tx},{ty}"

            if 0 <= tx < self.data['meta']['width'] and 0 <= ty < self.data['meta']['height'] and t_str in self.data[
                'locations']:
                ev = self.data['events'].get(p_str)
                if ev and ev.get('target') == [tx, ty] and not ev.get('warp') and t_str not in self.data['unlocked']:
                    print(f"BLOCKED: {self.data['event_descs'].get(p_str, 'Path locked.')}")
                else:
                    self.current_pos = [tx, ty]
                    if t_str not in self.data['visited']: self.data['visited'].append(t_str)
            else:
                print("Path blocked.")

        elif inp == 'get':
            if p_str in self.data['items'] and self.data['items'][p_str]:
                item = self.data['items'][p_str].pop()
                self.inventory.append(item)
                print(f"Got {item}!")
            else:
                print("Nothing here.")

        elif inp == 'talk' and p_str in self.data['npcs']:
            n = self.data['npcs'][p_str]
            print(f"[{n['name']}]: {n['dialogue'][n['index'] % len(n['dialogue'])]}")
            n['index'] += 1

        elif inp.startswith('use '):
            item = inp.replace('use ', '').strip()
            ev = self.data['events'].get(p_str)
            if item in self.inventory and ev and item == ev['req']:
                if ev['warp']:
                    self.current_pos = ev['target']; print("Warped!")
                else:
                    t_coord = f"{ev['target'][0]},{ev['target'][1]}"
                    if t_coord not in self.data['unlocked']: self.data['unlocked'].append(t_coord); print("Unlocked!")
            else:
                print("No effect.")

        elif inp in ['m', 'map']:
            self.show_map()
        elif inp in ['i', 'inv']:
            print(f"Inv: {self.inventory}")
        elif inp == 'warp':
            self.fast_travel()

        self.data["session_inventory"] = self.inventory
        self.save_world()

    def show_map(self):
        w, h = self.data["meta"]["width"], self.data["meta"]["height"]
        for y in range(h - 1, -1, -1):
            line = f"{y:1d} | "
            for x in range(w):
                p = f"{x},{y}"
                if [x, y] == self.current_pos:
                    line += "@ "
                elif p in self.data.get('visited', []):
                    line += "# "
                else:
                    line += ". "
            print(line)

    def fast_travel(self):
        v = sorted(self.data.get("visited", []))
        for i, pt in enumerate(v, 1): print(f"{i}. {pt} - {self.data['locations'].get(pt)}")
        c = input("Select #: ")
        if c.isdigit() and 1 <= int(c) <= len(v):
            self.current_pos = [int(x) for x in v[int(c) - 1].split(",")]


if __name__ == "__main__":
    game = WorldGrid()
    while True:
        game.show_room()
        u = input("\nAction > ").strip().lower()
        if u == 'q':
            break
        elif u == 'c':
            game.creator_mode()
        else:
            game.run_command(u)