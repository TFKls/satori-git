package satori.common;

import java.util.ArrayList;
import java.util.List;

public class SReferenceList {
	private List<SReference> refs = new ArrayList<SReference>();

	public boolean isEmpty() { return refs.isEmpty(); }
	public void add(SReference ref) { refs.add(ref); }
	public void remove(SReference ref) { refs.remove(ref); }
	public void notifyModified() { for (SReference ref : refs) ref.notifyModified(); }
	public void notifyDeleted() { for (SReference ref : refs) ref.notifyDeleted(); }
}
