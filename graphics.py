import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path
from data_processing import DataLoader, DataCleaner
from config_and_tools import Timer, Config

# Настройки для красивых графиков
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 7)
plt.rcParams["font.family"] = "DejaVu Sans"


def plot_correlation_matrix(df: pd.DataFrame, output_dir: Path):
    """График корреляции численных колонок"""
    numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns

    plt.figure(figsize=(14, 10))
    correlation_matrix = df[numeric_cols].corr()

    sns.heatmap(
        correlation_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8}
    )

    plt.title("Корреляция между переменными", fontsize=16, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "корреляция_колонок.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("✓ Сохранён график: корреляция_колонок.png")


def plot_payments_by_hour(df: pd.DataFrame, output_dir: Path):
    """График выплат водителям по часам суток"""
    hourly_data = df.groupby("час_суток")["выплата_водителю"].agg(["sum", "mean", "count"])

    fig, ax1 = plt.subplots(figsize=(14, 7))

    # Столбец - общая выплата
    color = "tab:blue"
    ax1.bar(hourly_data.index, hourly_data["sum"], color=color, alpha=0.7, label="Общая выплата")
    ax1.set_xlabel("Час суток", fontsize=12)
    ax1.set_ylabel("Сумма выплат ($)", color=color, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_xticks(range(0, 24, 2))

    # Линия - средняя выплата
    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.plot(hourly_data.index, hourly_data["mean"], color=color, marker="o",
             linewidth=2, markersize=6, label="Средняя выплата")
    ax2.set_ylabel("Средняя выплата на поездку ($)", color=color, fontsize=12)
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title("Оборот выплат в зависимости от времени суток", fontsize=16, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Легенда
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=11)

    plt.tight_layout()
    plt.savefig(output_dir / "выплаты_по_часам.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("✓ Сохранён график: выплаты_по_часам.png")


def plot_payments_by_weekday(df: pd.DataFrame, output_dir: Path):
    """График выплат по дням недели"""
    daily_data = df.groupby("день_недели")["выплата_водителю"].sum()
    daily_data = daily_data.reindex(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"])

    plt.figure(figsize=(8, 5))
    daily_data.plot(kind="bar", color="steelblue")

    plt.xlabel("День недели", fontsize=11)
    plt.ylabel("Сумма выплат ($)", fontsize=11)
    plt.title("Выплаты по дням недели", fontsize=13, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(output_dir / "выплаты_по_дням_недели.png", dpi=300)
    plt.close()
    print("✓ Сохранён график: выплаты_по_дням_недели.png")


def plot_payments_vs_kilometers(df: pd.DataFrame, output_dir: Path):
    """График зависимости выплат от километража"""
    plt.figure(figsize=(12, 7))

    # Используем scatter plot с прозрачностью
    plt.scatter(df["километры"], df["выплата_водителю"], alpha=0.5, s=30, color="green")

    # Добавляем линию тренда
    z = np.polyfit(df["километры"], df["выплата_водителю"], 1)
    p = np.poly1d(z)
    km_range = np.linspace(df["километры"].min(), df["километры"].max(), 100)
    plt.plot(km_range, p(km_range), "r-", linewidth=2, label=f"Тренд: y={z[0]:.2f}x+{z[1]:.2f}")

    plt.xlabel("Пройденные километры", fontsize=12)
    plt.ylabel("Выплата водителю ($)", fontsize=12)
    plt.title("Зависимость выплат от пройденных километров", fontsize=16, fontweight="bold")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "выплаты_от_километров.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("✓ Сохранён график: выплаты_от_километров.png")


def plot_payments_vs_duration(df: pd.DataFrame, output_dir: Path):
    """График зависимости выплат от времени поездки"""
    # Переводим секунды в минуты для удобства
    df["время_в_пути_мин"] = df["время_в_пути_сек"] / 60

    plt.figure(figsize=(12, 7))

    # Scatter plot
    plt.scatter(df["время_в_пути_мин"], df["выплата_водителю"], alpha=0.5, s=30, color="purple")

    # Линия тренда
    z = np.polyfit(df["время_в_пути_мин"], df["выплата_водителю"], 1)
    p = np.poly1d(z)
    time_range = np.linspace(df["время_в_пути_мин"].min(), df["время_в_пути_мин"].max(), 100)
    plt.plot(time_range, p(time_range), "r-", linewidth=2, label=f"Тренд: y={z[0]:.2f}x+{z[1]:.2f}")

    plt.xlabel("Время поездки (минуты)", fontsize=12)
    plt.ylabel("Выплата водителю ($)", fontsize=12)
    plt.title("Зависимость выплат от времени поездки", fontsize=16, fontweight="bold")
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "выплаты_от_времени_поездки.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("✓ Сохранён график: выплаты_от_времени_поездки.png")


if __name__ == "__main__":
    import numpy as np

    config = Config()
    config.raw_file_pattern = "*.parquet"

    # Создаём папку для графиков
    graphs_dir = config.output_path.parent / "графики"
    graphs_dir.mkdir(parents=True, exist_ok=True)

    # Загружаем данные
    print("Загружаем данные...")
    df = DataLoader(config).get_data()

    print(f"Загружено {len(df)} записей")
    print("\nСоздаём графики...\n")

    with Timer("Создание всех графиков"):
        plot_correlation_matrix(df, graphs_dir)
        plot_payments_by_hour(df, graphs_dir)
        plot_payments_by_weekday(df, graphs_dir)
        plot_payments_vs_kilometers(df, graphs_dir)
        plot_payments_vs_duration(df, graphs_dir)

    print(f"\n✓ Все графики сохранены в папку: {graphs_dir}")
