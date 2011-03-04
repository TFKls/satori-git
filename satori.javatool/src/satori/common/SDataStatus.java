package satori.common;

public class SDataStatus {
	private boolean modified = false;
	private boolean outdated = false;

	public boolean isModified() { return modified; }
	public boolean isOutdated() { return outdated; }

	public void markUpToDate() {
		modified = false;
		outdated = false;
	}
	public void markModified() {
		modified = true;
	}
	public void markOutdated() {
		outdated = true;
	}
}
