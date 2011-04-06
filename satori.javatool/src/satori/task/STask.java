package satori.task;

public interface STask {
	void run(STaskLogger logger) throws Throwable;
}
