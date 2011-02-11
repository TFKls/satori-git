package satori.common;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class SViewList {
	private List<SView> views = new ArrayList<SView>();
	
	public List<SView> get() { return Collections.unmodifiableList(views); }
	public void add(SView view) { views.add(view); }
	public void remove(SView view) { views.remove(view); }
	public void update() { for (SView view : views) view.update(); }
}
