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
	
	/*public String getStatusText(boolean is_remote) {
		String result = "";
		if (is_remote) {
			if (isOutdated()) result = "outdated";
		} else {
			if (isOutdated()) result = "deleted";
			else result = "new";
		}
		if (isModified()) {
			if (!result.isEmpty()) result += ", ";
			result += "modified";
		}
		if (result.isEmpty()) result = "saved";
		return result;
	}*/
}
