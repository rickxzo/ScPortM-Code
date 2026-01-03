const tab = {
  data() {
    return {
      stocks: [],
      search: "",
      sortKey: "name",
      sortOrder: "asc",
      tagFilter: "all",
      boughtMap: {}, // track bought state per stock
      loading: true,
      error: null
    };
  },

  computed: {
    processedStocks() {
      let list = [...this.stocks];

      // Search
      const q = this.search.toLowerCase();
      if (q) list = list.filter(s => s.name.toLowerCase().includes(q));

      // Tag filter
      if (this.tagFilter !== "all") {
        list = list.filter(s => s.tag === Number(this.tagFilter));
      }

      // Sort
      list.sort((a, b) => {
        const x = a[this.sortKey];
        const y = b[this.sortKey];

        if (typeof x === "string") {
          return this.sortOrder === "asc"
            ? x.localeCompare(y)
            : y.localeCompare(x);
        }
        return this.sortOrder === "asc" ? x - y : y - x;
      });

      return list;
    }
  },

  methods: {

    newMonitor() {
      const tinker = prompt("Enter ID:");
      if (tinker === null || tinker.trim() === "") {
        alert("ID is required.");
        return;
      }

      const id = prompt("Enter Tinker:");
      if (id === null || id.trim() === "") {
        alert("Tinker is required.");
        return;
      }

      fetch(`/mk?q=${encodeURIComponent(id)}&tk=${encodeURIComponent(tinker)}`)
        .catch(err => {
          alert("Failed to add monitor");
          console.error(err);
        });
    },

    
    buyStock(stock) {
      if (this.boughtMap[stock.name]) return;

      const qty = prompt(`Enter quantity to buy for ${stock.name}:`);
      const price = prompt(`Enter price (-1 for current price):`);
      var date = 0;
      if (price != "-1"){
        date = prompt(`Enter date:`);
      }
      if (qty === null || qty.trim() === "") {
        alert("Quantity is required.");
        return;
      }

      const n = Number(qty);

      // Invalid number
      if (isNaN(n) || n <= 0) {
        alert("Please enter a valid positive number.");
        return;
      }

      fetch(`/buy?q=${encodeURIComponent(stock.name)}&n=${n}&p=${price}&d=${date}`);

      this.boughtMap[stock.name] = true;

      setTimeout(() => {
        this.boughtMap[stock.name] = false;
      }, 1000);
    },


    removeStock(stock) {
        const ok = confirm(`Remove ${stock.name}?`);
        if (!ok) return;

        fetch(`/rm?q=${encodeURIComponent(stock.name)}`);
    }
  },

  mounted() {
    fetch("/data")
      .then(res => res.json())
      .then(data => {
        this.stocks = data;
        this.loading = false;
      })
      .catch(err => {
        this.error = err.message;
        this.loading = false;
      });
  },

  template: `
    <div class="w-full">

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-3 px-4 py-3 bg-white sticky top-0 z-10 border-b">

        <button
          @click="newMonitor"
          class="px-3 py-1.5 text-sm font-semibold rounded
                bg-blue-600 text-white hover:bg-blue-700 transition"
        >
          New monitor
        </button>   

        <!-- Sort -->
        <div class="flex items-center gap-2">
          <select v-model="sortKey" class="text-sm border rounded px-2 py-1">
            <option value="name">Name</option>
            <option value="price">Price</option>
            <option value="market_cap">Market Cap</option>
            <option value="pe">PE</option>
            <option value="roe">ROE</option>
            <option value="roce">ROCE</option>
            <option value="qtr_profit_var">QoQ Profit</option>
            <option value="qtr_sales_var">QoQ Sales</option>
          </select>

          <button
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            class="px-2 py-1 text-sm border rounded hover:bg-gray-100"
          >
            {{ sortOrder === "asc" ? "↑" : "↓" }}
          </button>
        </div>

        <!-- Search -->
        <input
          v-model="search"
          placeholder="Search stock..."
          class="flex-1 min-w-[180px] px-3 py-1.5 text-sm border rounded
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <!-- Tag filter -->
        <select v-model="tagFilter" class="text-sm border rounded px-2 py-1">
          <option value="all">All</option>
          <option value="1">Positive</option>
          <option value="0">Neutral</option>
          <option value="-1">Negative</option>
        </select>
      </div>

      <!-- List -->
      <div class="p-2">
        <div
          v-for="stock in processedStocks"
          :key="stock.name"
          class="mb-2 px-4 py-3 rounded border text-xs transition"
          :class="{
            'bg-green-50 hover:bg-green-100': stock.tag === 1,
            'bg-red-50 hover:bg-red-100': stock.tag === -1,
            'bg-white hover:bg-gray-50': stock.tag === 0
          }"
        >

          <!-- Header -->
          <div class="flex justify-between items-center">
            <div>
                <div class="text-sm font-semibold">{{ stock.name }}</div>
                <div class="text-sm font-semibold">₹{{ stock.price }}</div>
            </div>

            <div class="flex gap-2">
                <!-- Buy button -->
                <button
                @click="buyStock(stock)"
                :disabled="boughtMap[stock.name]"
                class="px-3 py-1.5 text-xs font-semibold rounded transition"
                :class="boughtMap[stock.name]
                    ? 'bg-gray-300 text-gray-700 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'"
                >
                {{ boughtMap[stock.name] ? 'Bought' : 'Buy' }}
                </button>

                <!-- Remove button -->
                <button
                @click="removeStock(stock)"
                class="px-3 py-1.5 text-xs font-semibold rounded
                        bg-red-600 text-white hover:bg-red-700 transition"
                >
                Remove
                </button>
            </div>
            </div>


          <!-- Ratios -->
          <div class="grid grid-cols-4 gap-4 mt-2">
            <span>PE <b>{{ stock.pe }}</b></span>
            <span>Book <b>₹{{ stock.book }}</b></span>
            <span>ROE <b>{{ stock.roe }}%</b></span>
            <span>ROCE <b>{{ stock.roce }}%</b></span>
          </div>

          <!-- High / Low -->
          <div class="grid grid-cols-4 gap-4 mt-1">
            <span>High <b>₹{{ stock.high }}</b></span>
            <span>Low <b>₹{{ stock.low }}</b></span>
            <span>Dev <b>{{ stock.deviation }}</b></span>
            <span>Holdings <b>{{ stock.num ?? 0 }}</b></span>
          </div>

          <!-- Quarterly -->
          <div class="grid grid-cols-4 gap-4 mt-1">
            <span>Sales Q <b>₹{{ stock.sales_qtr?.toLocaleString() }}</b></span>
            <span>Profit Q <b>₹{{ stock.np_qtr?.toLocaleString() }}</b></span>
            <span>Sales QoQ <b>{{ stock.qtr_sales_var ?? 0 }}%</b></span>
            <span>Profit QoQ <b>{{ stock.qtr_profit_var ?? 0 }}%</b></span>
          </div>

          <div class="mt-1 text-gray-500">
            Market Cap ₹{{ stock.market_cap?.toLocaleString() }}
          </div>
        </div>
      </div>

    </div>
  `
};

const tab2 = {
  data() {
    return {
      rows: [],
      search: "",
      loading: true,
      error: null
    };
  },

  computed: {
    filteredRows() {
      if (!this.search) return this.rows;
      const q = this.search.toLowerCase();
      return this.rows.filter(r =>
        r.name.toLowerCase().includes(q) ||
        String(r.lid).includes(q)
      );
    }
  },

  methods: {
    loadPortfolio() {
      this.loading = true;

      fetch("/holding")
        .then(res => res.json())
        .then(data => {
          this.rows = data.map(r => ({
            lid: r[0],
            name: r[1],
            date: r[2],
            price: r[3],
            amt: r[4]
          }));
          this.loading = false;
        })
        .catch(err => {
          this.error = err.message;
          this.loading = false;
        });
    },

    total(row) {
      return row.price * row.amt;
    },

    sell(row) {
      const ok = confirm(
        `Sell lot ${row.lid} of ${row.name}?`
      );
      if (!ok) return;

      var date = 0;
      const qty = prompt(`Enter selling price (-1 for curr price):`);
      if (qty != "-1"){
        date = prompt(`Enter date:`);
      }

      fetch(`/sell?q=${encodeURIComponent(row.name)}&n=${row.lid}&p=${qty}&d=${date}`)
        .then(() => {
          // refresh portfolio after sell
          this.loadPortfolio();
        })
        .catch(err => {
          alert("Sell failed");
          console.error(err);
        });
    }
  },

  mounted() {
    this.loadPortfolio();
  },

  template: `
    <div class="w-full">

      <!-- Search -->
      <div class="px-4 py-3 bg-white sticky top-0 z-10 border-b">
        <input
          v-model="search"
          placeholder="Search by lot ID or stock name..."
          class="w-full px-3 py-2 text-sm border rounded
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-4 text-sm text-gray-500">
        Loading portfolio...
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-4 text-sm text-red-600">
        {{ error }}
      </div>

      <!-- Portfolio list -->
      <div v-else class="p-2 space-y-2">

        <div
          v-for="row in filteredRows"
          :key="row.lid"
          class="px-4 py-3 border rounded bg-white hover:bg-gray-50 transition text-sm"
        >
          <div class="flex justify-between items-center">

            <div class="grid grid-cols-6 gap-6 flex-1">
              <div>
                <div class="text-xs text-gray-500">Lot ID</div>
                <div class="font-semibold">{{ row.lid }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500">Name</div>
                <div class="font-semibold">{{ row.name }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500">Buy Date</div>
                <div>{{ row.date }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500">Buy Price</div>
                <div>₹{{ row.price }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500">Amount</div>
                <div>{{ row.amt }}</div>
              </div>

              <div>
                <div class="text-xs text-gray-500">Total</div>
                <div class="font-semibold">
                  ₹{{ total(row).toLocaleString() }}
                </div>
              </div>
            </div>

            <button
              @click="sell(row)"
              class="ml-4 px-4 py-2 text-sm font-semibold rounded
                     bg-blue-600 text-white hover:bg-blue-700"
            >
              Sell
            </button>

          </div>
        </div>

      </div>
    </div>
  `
};

const tab3 = {
  data() {
    return {
      rows: [],
      search: "",
      loading: true,
      error: null
    };
  },

  computed: {
    filteredRows() {
      if (!this.search) return this.rows;
      const q = this.search.toLowerCase();
      return this.rows.filter(r =>
        r.name.toLowerCase().includes(q)
      );
    },

    totalBuy() {
      return this.filteredRows.reduce(
        (sum, r) => sum + r.buy_price * r.amt,
        0
      );
    },

    totalProfit() {
      return this.filteredRows.reduce(
        (sum, r) => sum + (r.profit ?? 0),
        0
      );
    }
  },

  mounted() {
    fetch("/hist_data")
      .then(res => res.json())
      .then(data => {
        this.rows = data.map(r => ({
          name: r[0],
          buy_date: r[1],
          buy_price: r[2],
          amt: r[3],
          sell_date: r[4],
          profit: r[5],
          duration: r[6],
          sell_price: r[7],
          sid: r[8]
        }));
        this.loading = false;
      })
      .catch(err => {
        this.error = err.message;
        this.loading = false;
      });
  },

  methods: {
    totalBuyRow(row) {
      return row.buy_price * row.amt;
    },

    hideRow(row) {
      const ok = confirm(
        `Hide this record for ${row.name}?\nThis cannot be viewed again.`
      );
      if (!ok) return;

      fetch(`/hide?q=${row.sid}`)
        .then(() => {
          // refresh history after hide
          alert("Record hidden");
        })
        .catch(err => {
          alert("Failed to hide record");
          console.error(err);
        });
    }
  },

  template: `
    <div class="w-full">

      <!-- Summary -->
      <div class="px-4 py-3 bg-white sticky top-0 z-10 border-b space-y-2">

        <div class="flex gap-8 text-sm">
          <div>
            <div class="text-xs text-gray-500">Total Buy</div>
            <div class="font-semibold">
              ₹{{ totalBuy.toLocaleString() }}
            </div>
          </div>

          <div>
            <div class="text-xs text-gray-500">Total Profit</div>
            <div
              class="font-semibold"
              :class="totalProfit > 0
                ? 'text-green-600'
                : totalProfit < 0
                  ? 'text-red-600'
                  : 'text-gray-600'"
            >
              ₹{{ totalProfit.toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Search -->
        <input
          v-model="search"
          placeholder="Search by stock name..."
          class="w-full px-3 py-2 text-sm border rounded
                 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="p-4 text-sm text-gray-500">
        Loading history...
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-4 text-sm text-red-600">
        {{ error }}
      </div>

      <!-- History list -->
      <div v-else class="p-2 space-y-2">

        <div
          v-for="(row, idx) in filteredRows"
          :key="idx"
          class="px-4 py-3 border rounded bg-white text-sm"
        >
          <div class="grid grid-cols-9 gap-6">

            <div>
              <div class="text-xs text-gray-500">Name</div>
              <div class="font-semibold">{{ row.name }}</div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Buy Date</div>
              <div>{{ row.buy_date }}</div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Buy Price</div>
              <div>₹{{ row.buy_price }}</div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Amount</div>
              <div>{{ row.amt }}</div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Total Buy</div>
              <div class="font-semibold">
                ₹{{ totalBuyRow(row).toLocaleString() }}
              </div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Sell price</div>
              <div>
                ₹{{ row.sell_price === null ? "—" : row.sell_price }}
              </div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Duration (days)</div>
              <div>
                {{ row.duration === null ? "—" : row.duration }}
              </div>
            </div>

            <div>
              <div class="text-xs text-gray-500">Profit</div>
              <div
                :class="row.profit > 0
                  ? 'text-green-600 font-semibold'
                  : row.profit < 0
                    ? 'text-red-600 font-semibold'
                    : 'text-gray-400'"
              >
                {{ row.profit === null ? "—" : "₹" + row.profit }}
              </div>
            </div>

            <div class="flex items-end">
              <button
                @click="hideRow(row)"
                class="px-3 py-1.5 text-xs font-semibold rounded
                      bg-gray-600 text-white hover:bg-gray-700"
              >
                Hide
              </button>
            </div>

          </div>
        </div>

      </div>
    </div>
  `
};





const app = Vue.createApp({});
app.component("tab", tab);
app.component("tab2", tab2);
app.component("tab3", tab3);
app.mount("#app");

