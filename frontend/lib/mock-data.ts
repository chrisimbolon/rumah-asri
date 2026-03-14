// ─────────────────────────────────────────────────────────────
//  RumahAsri — Mock Data (Bahasa Indonesia)
//  PT Asri Sentosa Properti · Jambi, Indonesia
//  Data demo untuk presentasi investor
// ─────────────────────────────────────────────────────────────

// ── Developer ────────────────────────────────────────────────
export const DEVELOPER = {
  id: "dev-001",
  nama: "PT Asri Sentosa Properti",
  kota: "Jambi",
  alamat: "Jl. Hayam Wuruk No. 12, Jambi Selatan, Kota Jambi 36138",
  telepon: "+62 741 555 1234",
  email: "admin@asrisentosa.co.id",
  npwp: "01.234.567.8-331.000",
  plan: "Profesional",
  harga_plan: "Rp 2.500.000 / bulan",
  maks_unit: 500,
  maks_agen: 20,
  bergabung: "Januari 2025",
  perpanjangan: "1 Januari 2027",
};

// ── Statistik ringkasan ───────────────────────────────────────
export const STATISTIK = {
  total_proyek: 4,
  unit_terjual: 89,
  unit_konstruksi: 47,
  total_unit: 142,
  pendapatan_bulan: "Rp 12,4M",
  pertumbuhan: "+14%",
  agen_aktif: 8,
  total_pembeli: 89,
};

// ── Proyek ────────────────────────────────────────────────────
export type Proyek = {
  id: string;
  nama: string;
  lokasi: string;
  total_unit: number;
  terjual: number;
  progres: number;
  status: string;
  mulai: string;
  selesai: string;
  deskripsi: string;
};

export const PROYEK: Proyek[] = [
  {
    id: "pry-001",
    nama: "Perumahan Asri Cluster A",
    lokasi: "Telanaipura, Jambi",
    total_unit: 40,
    terjual: 35,
    progres: 88,
    status: "aktif",
    mulai: "15 Jan 2025",
    selesai: "Des 2025",
    deskripsi:
      "Cluster premium dengan konsep modern minimalis di jantung kota Jambi. Dekat pusat perbelanjaan dan sekolah unggulan.",
  },
  {
    id: "pry-002",
    nama: "Perumahan Asri Cluster B",
    lokasi: "Alam Barajo, Jambi",
    total_unit: 38,
    terjual: 28,
    progres: 65,
    status: "aktif",
    mulai: "1 Mar 2025",
    selesai: "Feb 2026",
    deskripsi:
      "Hunian asri di kawasan hijau Alam Barajo dengan konsep eco-living. Setiap unit dilengkapi taman pribadi.",
  },
  {
    id: "pry-003",
    nama: "Perumahan Asri Cluster C",
    lokasi: "Kotabaru, Jambi",
    total_unit: 44,
    terjual: 18,
    progres: 35,
    status: "aktif",
    mulai: "1 Jun 2025",
    selesai: "Mei 2026",
    deskripsi:
      "Kawasan perumahan strategis dekat Jembatan Batanghari dengan akses mudah ke pusat kota.",
  },
  {
    id: "pry-004",
    nama: "Perumahan Asri Grand D",
    lokasi: "Jambi Timur, Jambi",
    total_unit: 20,
    terjual: 8,
    progres: 20,
    status: "perencanaan",
    mulai: "1 Sep 2025",
    selesai: "Agu 2026",
    deskripsi:
      "Proyek percontohan dengan konsep smart home pertama di Kota Jambi.",
  },
];

// ── Unit ──────────────────────────────────────────────────────
export type Unit = {
  id: string;
  proyek_id: string;
  proyek_nama: string;
  nomor: string;
  tipe: string;
  luas_tanah: number;
  luas_bgn: number;
  harga: number;
  status: string;
  pembeli_id: string | null;
  pembeli_nama: string | null;
  progres: number;
  fase: string;
  selesai: string;
};

export const UNIT: Unit[] = [
  {
    id: "unt-001",
    proyek_id: "pry-001",
    proyek_nama: "Cluster A",
    nomor: "A-01",
    tipe: "Tipe 45",
    luas_tanah: 72,
    luas_bgn: 45,
    harga: 850000000,
    status: "proses",
    pembeli_id: "pmb-001",
    pembeli_nama: "Budi Santoso",
    progres: 85,
    fase: "Finishing interior",
    selesai: "Agu 2025",
  },
  {
    id: "unt-002",
    proyek_id: "pry-001",
    proyek_nama: "Cluster A",
    nomor: "A-05",
    tipe: "Tipe 45",
    luas_tanah: 72,
    luas_bgn: 45,
    harga: 850000000,
    status: "proses",
    pembeli_id: "pmb-004",
    pembeli_nama: "Siti Marlina",
    progres: 22,
    fase: "Pembersihan lahan selesai",
    selesai: "Nov 2025",
  },
  {
    id: "unt-003",
    proyek_id: "pry-002",
    proyek_nama: "Cluster B",
    nomor: "B-07",
    tipe: "Tipe 54",
    luas_tanah: 90,
    luas_bgn: 54,
    harga: 920000000,
    status: "terjual",
    pembeli_id: "pmb-002",
    pembeli_nama: "Rina Wulandari",
    progres: 68,
    fase: "Dinding struktural",
    selesai: "Sep 2025",
  },
  {
    id: "unt-004",
    proyek_id: "pry-003",
    proyek_nama: "Cluster C",
    nomor: "C-03",
    tipe: "Tipe 36",
    luas_tanah: 60,
    luas_bgn: 36,
    harga: 780000000,
    status: "proses",
    pembeli_id: "pmb-003",
    pembeli_nama: "Ahmad Fauzi",
    progres: 42,
    fase: "Pondasi selesai",
    selesai: "Okt 2025",
  },
  {
    id: "unt-005",
    proyek_id: "pry-003",
    proyek_nama: "Cluster C",
    nomor: "C-15",
    tipe: "Tipe 45",
    luas_tanah: 72,
    luas_bgn: 45,
    harga: 780000000,
    status: "tersedia",
    pembeli_id: null,
    pembeli_nama: null,
    progres: 0,
    fase: "-",
    selesai: "-",
  },
  {
    id: "unt-006",
    proyek_id: "pry-004",
    proyek_nama: "Grand D",
    nomor: "D-01",
    tipe: "Tipe 60",
    luas_tanah: 108,
    luas_bgn: 60,
    harga: 1100000000,
    status: "serah_terima",
    pembeli_id: "pmb-005",
    pembeli_nama: "Hendra Gunawan",
    progres: 97,
    fase: "Siap serah terima",
    selesai: "Mar 2026",
  },
];

// ── Timeline konstruksi Unit A-01 ─────────────────────────────
export type FaseTimeline = {
  fase: string;
  tgl: string;
  status: "selesai" | "proses" | "menunggu";
  catatan: string;
};

export const TIMELINE_A01: FaseTimeline[] = [
  {
    fase: "Pembersihan & persiapan lahan",
    tgl: "Jan 2025",
    status: "selesai",
    catatan: "Lahan dibersihkan & diratakan. Uji tanah lulus.",
  },
  {
    fase: "Pekerjaan pondasi",
    tgl: "Feb 2025",
    status: "selesai",
    catatan: "Pondasi beton dituang. 3 foto lapangan diunggah.",
  },
  {
    fase: "Rangka struktur",
    tgl: "Apr 2025",
    status: "selesai",
    catatan: "Rangka baja & kolom selesai dikerjakan.",
  },
  {
    fase: "Dinding struktural",
    tgl: "Mei 2025",
    status: "selesai",
    catatan: "Pasangan bata & plesteran selesai.",
  },
  {
    fase: "Pemasangan atap & waterproofing",
    tgl: "Jun 2025",
    status: "selesai",
    catatan: "Genteng dipasang, waterproofing atap selesai.",
  },
  {
    fase: "Finishing interior",
    tgl: "Jul – Agu 2025",
    status: "proses",
    catatan:
      "Pengecatan lantai bawah selesai. Pemasangan keramik sedang berjalan.",
  },
  {
    fase: "Selesai / serah terima",
    tgl: "Sep 2025",
    status: "menunggu",
    catatan: "",
  },
];

// ── Pembeli ───────────────────────────────────────────────────
export type Pembeli = {
  id: string;
  nama: string;
  email: string;
  telp: string;
  unit: string;
  unit_id: string;
  metode: string;
  bank: string;
  status: string;
};

export const PEMBELI: Pembeli[] = [
  {
    id: "pmb-001",
    nama: "Budi Santoso",
    email: "budi@gmail.com",
    telp: "+62 812 3456 7890",
    unit: "A-01",
    unit_id: "unt-001",
    metode: "KPR BCA",
    bank: "BCA",
    status: "lancar",
  },
  {
    id: "pmb-002",
    nama: "Rina Wulandari",
    email: "rina@gmail.com",
    telp: "+62 813 5678 9012",
    unit: "B-07",
    unit_id: "unt-003",
    metode: "KPR BNI",
    bank: "BNI",
    status: "lancar",
  },
  {
    id: "pmb-003",
    nama: "Ahmad Fauzi",
    email: "ahmad@gmail.com",
    telp: "+62 878 9012 3456",
    unit: "C-03",
    unit_id: "unt-004",
    metode: "Cash bertahap",
    bank: "-",
    status: "menunggak",
  },
  {
    id: "pmb-004",
    nama: "Siti Marlina",
    email: "siti@gmail.com",
    telp: "+62 857 3456 7890",
    unit: "A-05",
    unit_id: "unt-002",
    metode: "KPR Mandiri",
    bank: "Mandiri",
    status: "proses_bank",
  },
  {
    id: "pmb-005",
    nama: "Hendra Gunawan",
    email: "hendra@gmail.com",
    telp: "+62 811 2345 6789",
    unit: "D-01",
    unit_id: "unt-006",
    metode: "Cash keras",
    bank: "-",
    status: "lunas",
  },
];

// ── Agen ──────────────────────────────────────────────────────
export type Agen = {
  id: string;
  nama: string;
  inisial: string;
  email: string;
  telp: string;
  area: string;
  terjual: number;
  pendapatan: string;
  leads: number;
  proyek: number;
  status: string;
};

export const AGEN: Agen[] = [
  {
    id: "agn-001",
    nama: "Rizky Setiawan",
    inisial: "RS",
    email: "rizky@asrisentosa.co.id",
    telp: "+62 812 1111 2222",
    area: "Telanaipura & Jambi Selatan",
    terjual: 7,
    pendapatan: "Rp 4,2M",
    leads: 14,
    proyek: 2,
    status: "aktif",
  },
  {
    id: "agn-002",
    nama: "Dewi Puspita",
    inisial: "DP",
    email: "dewi@asrisentosa.co.id",
    telp: "+62 813 3333 4444",
    area: "Alam Barajo & Kotabaru",
    terjual: 5,
    pendapatan: "Rp 3,1M",
    leads: 9,
    proyek: 3,
    status: "aktif",
  },
  {
    id: "agn-003",
    nama: "Anton Hidayat",
    inisial: "AH",
    email: "anton@asrisentosa.co.id",
    telp: "+62 878 5555 6666",
    area: "Jambi Timur",
    terjual: 3,
    pendapatan: "Rp 1,8M",
    leads: 11,
    proyek: 2,
    status: "aktif",
  },
  {
    id: "agn-004",
    nama: "Linda Kusuma",
    inisial: "LK",
    email: "linda@asrisentosa.co.id",
    telp: "+62 857 7777 8888",
    area: "Jambi Selatan",
    terjual: 2,
    pendapatan: "Rp 1,2M",
    leads: 7,
    proyek: 1,
    status: "cuti",
  },
];

// ── Pembayaran ────────────────────────────────────────────────
export type Pembayaran = {
  id: string;
  pembeli: string;
  unit: string;
  jenis: string;
  jatuh_tempo: string;
  jumlah: number;
  status: string;
  bank: string;
};

export const PEMBAYARAN: Pembayaran[] = [
  {
    id: "pay-001",
    pembeli: "Budi Santoso",
    unit: "A-01",
    jenis: "Cicilan KPR #8",
    jatuh_tempo: "1 Mar 2026",
    jumlah: 7200000,
    status: "lunas",
    bank: "BCA",
  },
  {
    id: "pay-002",
    pembeli: "Rina Wulandari",
    unit: "B-07",
    jenis: "Cicilan KPR #5",
    jatuh_tempo: "1 Mar 2026",
    jumlah: 6800000,
    status: "lunas",
    bank: "BNI",
  },
  {
    id: "pay-003",
    pembeli: "Ahmad Fauzi",
    unit: "C-03",
    jenis: "Cash bertahap #2",
    jatuh_tempo: "25 Feb 2026",
    jumlah: 156000000,
    status: "menunggak",
    bank: "-",
  },
  {
    id: "pay-004",
    pembeli: "Siti Marlina",
    unit: "A-05",
    jenis: "Uang muka",
    jatuh_tempo: "15 Mar 2026",
    jumlah: 78000000,
    status: "menunggu",
    bank: "Mandiri",
  },
  {
    id: "pay-005",
    pembeli: "Hendra Gunawan",
    unit: "D-01",
    jenis: "Pelunasan akhir",
    jatuh_tempo: "20 Mar 2026",
    jumlah: 220000000,
    status: "akan_datang",
    bank: "-",
  },
];

// ── Biaya konstruksi ──────────────────────────────────────────
export type BiayaItem = {
  item: string;
  anggaran: number;
  realisasi: number | null;
  status: string;
};

export const BIAYA: BiayaItem[] = [
  {
    item: "Material pondasi",
    anggaran: 45000000,
    realisasi: 43200000,
    status: "sesuai",
  },
  {
    item: "Baja struktural",
    anggaran: 120000000,
    realisasi: 134500000,
    status: "melebihi",
  },
  {
    item: "Beton & pasangan bata",
    anggaran: 80000000,
    realisasi: 76800000,
    status: "sesuai",
  },
  {
    item: "Atap & genteng",
    anggaran: 55000000,
    realisasi: 52000000,
    status: "sesuai",
  },
  {
    item: "Instalasi listrik",
    anggaran: 35000000,
    realisasi: 38500000,
    status: "melebihi",
  },
  {
    item: "Instalasi pipa (plumbing)",
    anggaran: 28000000,
    realisasi: 27100000,
    status: "sesuai",
  },
  {
    item: "Finishing interior",
    anggaran: 65000000,
    realisasi: null,
    status: "berjalan",
  },
];

// ── Notifikasi ────────────────────────────────────────────────
export type Notifikasi = {
  id: string;
  judul: string;
  pesan: string;
  waktu: string;
  dibaca: boolean;
  tipe: "info" | "sukses" | "peringatan";
};

export const NOTIFIKASI: Notifikasi[] = [
  {
    id: "n1",
    judul: "Progres konstruksi diperbarui",
    pesan: "Unit A-01 diperbarui ke 85% — fase finishing interior",
    waktu: "2 jam lalu",
    dibaca: false,
    tipe: "info",
  },
  {
    id: "n2",
    judul: "Pembeli baru terdaftar",
    pesan: "Siti Marlina dihubungkan ke Unit A-05",
    waktu: "5 jam lalu",
    dibaca: false,
    tipe: "sukses",
  },
  {
    id: "n3",
    judul: "Pembayaran menunggak!",
    pesan: "Unit C-03 cicilan #2 menunggak 16 hari",
    waktu: "1 hari lalu",
    dibaca: false,
    tipe: "peringatan",
  },
  {
    id: "n4",
    judul: "Penjualan baru tercatat",
    pesan: "Unit B-07 terjual Agen Dewi — Rp 920 juta",
    waktu: "2 hari lalu",
    dibaca: false,
    tipe: "sukses",
  },
  {
    id: "n5",
    judul: "Laporan bulanan siap",
    pesan: "Laporan Februari 2026 siap diunduh",
    waktu: "3 hari lalu",
    dibaca: true,
    tipe: "info",
  },
];

// ── Log aktivitas ─────────────────────────────────────────────
export type LogItem = {
  waktu: string;
  pengguna: string;
  aksi: string;
};

export const LOG: LogItem[] = [
  {
    waktu: "10:32 hari ini",
    pengguna: "Teknisi Arif",
    aksi: "Mengunggah 3 foto untuk Unit A-01",
  },
  {
    waktu: "09:14 hari ini",
    pengguna: "Admin ASP",
    aksi: "Memperbarui progres Unit A-01 → 85%",
  },
  {
    waktu: "Kemarin",
    pengguna: "Agen Rizky",
    aksi: "Membuat data pembeli baru: Siti Marlina",
  },
  {
    waktu: "Kemarin",
    pengguna: "Agen Dewi",
    aksi: "Mencatat penjualan Unit B-07 — Rp 920.000.000",
  },
  {
    waktu: "2 hari lalu",
    pengguna: "Sistem",
    aksi: "Mengirim pengingat pembayaran ke Ahmad Fauzi (C-03)",
  },
  {
    waktu: "3 hari lalu",
    pengguna: "Admin ASP",
    aksi: "Membuat proyek baru: Perumahan Asri Grand D",
  },
];

// ── Grafik penjualan ──────────────────────────────────────────
export type DataGrafik = {
  bulan: string;
  penjualan: number;
};

export const GRAFIK_PENJUALAN: DataGrafik[] = [
  { bulan: "Okt", penjualan: 5 },
  { bulan: "Nov", penjualan: 7 },
  { bulan: "Des", penjualan: 4 },
  { bulan: "Jan", penjualan: 9 },
  { bulan: "Feb", penjualan: 11 },
  { bulan: "Mar", penjualan: 13 },
];

// ─────────────────────────────────────────────────────────────
//  Helper functions
// ─────────────────────────────────────────────────────────────

/** Format angka ke Rupiah — Rp 850.000.000 */
export function rupiah(n: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

/** Kembalikan CSS class badge berdasarkan status */
export function badgeStatus(s: string): string {
  const map: Record<string, string> = {
    aktif:        "badge-green",
    terjual:      "badge-green",
    tersedia:     "badge-gray",
    proses:       "badge-blue",
    serah_terima: "badge-gold",
    perencanaan:  "badge-amber",
    selesai:      "badge-green",
    menunggu:     "badge-gray",
    lunas:        "badge-green",
    menunggak:    "badge-red",
    proses_bank:  "badge-amber",
    akan_datang:  "badge-blue",
    melebihi:     "badge-red",
    sesuai:       "badge-green",
    berjalan:     "badge-blue",
    cuti:         "badge-amber",
    lancar:       "badge-green",
  };
  return map[s] ?? "badge-gray";
}

/** Kembalikan label Bahasa Indonesia dari status key */
export function labelStatus(s: string): string {
  const map: Record<string, string> = {
    aktif:        "Aktif",
    terjual:      "Terjual",
    tersedia:     "Tersedia",
    proses:       "Proses",
    serah_terima: "Serah Terima",
    perencanaan:  "Perencanaan",
    selesai:      "Selesai",
    menunggu:     "Menunggu",
    lunas:        "Lunas",
    menunggak:    "Menunggak",
    proses_bank:  "Proses Bank",
    akan_datang:  "Akan Datang",
    melebihi:     "Melebihi Anggaran",
    sesuai:       "Sesuai Anggaran",
    berjalan:     "Berjalan",
    cuti:         "Cuti",
    lancar:       "Lancar",
  };
  return map[s] ?? s;
}

/** Warna progress bar berdasarkan persentase */
export function warnaProgres(pct: number): string {
  if (pct >= 80) return "var(--color-success)";
  if (pct >= 50) return "var(--color-accent)";
  return "var(--color-warning)";
}
