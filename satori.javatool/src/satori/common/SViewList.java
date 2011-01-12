package satori.common;

import java.util.List;
import java.util.ArrayList;

public class SViewList {
	private List<SView> views = new ArrayList<SView>();
	
	public void add(SView view) { views.add(view); }
	public void remove(SView view) { views.remove(view); }
	public void update() { for (SView view : views) view.update(); }
}
