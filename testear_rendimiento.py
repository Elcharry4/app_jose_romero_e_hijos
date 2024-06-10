import cProfile
import pstats
from main import MyApp

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    MyApp().run()
    profiler.disable()
    with open("profile_stats.txt", "w") as stream:
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats()
