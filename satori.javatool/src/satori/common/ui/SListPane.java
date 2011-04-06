package satori.common.ui;

import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.Insets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.swing.AbstractListModel;
import javax.swing.DefaultListCellRenderer;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.ListCellRenderer;

import satori.common.SListView;
import satori.common.SModel;
import satori.common.SView;

@SuppressWarnings("serial")
public class SListPane<T extends SModel> extends JList {
	public interface Column<T> {
		String get(T data);
	}
	
	private static class ListModel<T> extends AbstractListModel implements SView {
		private final List<T> list = new ArrayList<T>();
		private final Comparator<T> comparator;
		private final boolean sort_on_update;
		
		public ListModel(Comparator<T> comparator, boolean sort_on_update) {
			this.comparator = comparator;
			this.sort_on_update = sort_on_update;
		}
		
		@Override public int getSize() { return list.size(); }
		@Override public T getElementAt(int index) { return list.get(index); }
		public List<T> getAllElements() { return list; }
		
		public void addItem(T item) { list.add(item); }
		public void removeItem(T item) { list.remove(item); }
		public void removeAllItems() { list.clear(); }
		
		@Override public void update() {
			if (sort_on_update) Collections.sort(list, comparator);
			fireContentsChanged(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterAdd() {
			Collections.sort(list, comparator);
			fireIntervalAdded(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterRemove() {
			fireIntervalRemoved(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
	}
	
	private static class CellLayout extends SLayoutManagerAdapter {
		private final Map<Component, Float> ratios = new HashMap<Component, Float>();
		private int height;
		private boolean unknown = true;
		
		private void setHeight(Container target) {
			if (!unknown) return;
			height = 0;
			for (int i=0; i<target.getComponentCount(); ++i) {
				Component comp = target.getComponent(i);
				height = Math.max(height, comp.getPreferredSize().height);
			}
			unknown = false;
		}
		
		@Override public void addLayoutComponent(Component comp, Object constraints) {
			ratios.put(comp, (Float)constraints);
		}
		@Override public void removeLayoutComponent(Component comp) {
			ratios.remove(comp);
		}
		@Override public Dimension preferredLayoutSize(Container target) {
			setHeight(target);
			Insets insets = target.getInsets();
			int width = insets.left + insets.right;
			int height = this.height + insets.top + insets.bottom;
			return new Dimension(width, height);
		}
		@Override public void invalidateLayout(Container target) {
			unknown = true;
		}
		@Override public void layoutContainer(Container target) {
			setHeight(target);
			Insets insets = target.getInsets();
			int width = target.getWidth() - insets.left - insets.right;
			int height = target.getHeight() - insets.top - insets.bottom;
			float x = insets.left;
			for (int i=0; i<target.getComponentCount(); ++i) {
				Component comp = target.getComponent(i);
				float nextX = x + width*ratios.get(comp);
				comp.setBounds(Math.round(x), insets.top, Math.round(nextX) - Math.round(x), height);
				x = nextX;
			}
		}
	}
	
	private static class CellRenderer<T> implements ListCellRenderer {
		private final List<Column<T>> columns = new ArrayList<Column<T>>();
		private final ListCellRenderer template = new DefaultListCellRenderer();
		private final JComponent pane = new JPanel(new CellLayout());
		
		public void addColumn(Column<T> column, float ratio) {
			columns.add(column);
			pane.add(new JLabel(), ratio);
		}
		
		@Override public Component getListCellRendererComponent(JList list, Object value, int index, boolean isSelected, boolean cellHasFocus) {
			JComponent comp = (JComponent)template.getListCellRendererComponent(list, null, index, isSelected, cellHasFocus);
			@SuppressWarnings("unchecked") T item = (T)value;
			pane.setBackground(comp.getBackground());
			pane.setBorder(comp.getBorder());
			for (int i = 0; i < columns.size(); ++i) {
				JLabel label = (JLabel)comp.getComponent(i);
				label.setForeground(comp.getForeground());
				label.setFont(comp.getFont());
				label.setText(columns.get(i).get(item));
			}
			return pane;
		}
	}
	
	private final ListModel<T> model;
	private final CellRenderer<T> renderer;
	
	public SListPane(Comparator<T> comparator, boolean sort_on_update) {
		model = new ListModel<T>(comparator, sort_on_update);
		renderer = new CellRenderer<T>();
		setModel(model);
		setCellRenderer(renderer);
	}
	
	public T getItem(int index) { return model.getElementAt(index); }
	
	public void addColumn(Column<T> column, float ratio) {
		renderer.addColumn(column, ratio);
	}
	
	private final SListView<T> list_view = new SListView<T>() {
		@Override public void add(T item) {
			clearSelection();
			model.addItem(item);
			item.addView(model);
			model.updateAfterAdd();
		}
		@Override public void add(Iterable<T> items) {
			clearSelection();
			for (T item : items) {
				model.addItem(item);
				item.addView(model);
			}
			model.updateAfterAdd();
		}
		@Override public void remove(T item) {
			clearSelection();
			item.removeView(model);
			model.removeItem(item);
			model.updateAfterRemove();
		}
		@Override public void removeAll() {
			clearSelection();
			for (T item : model.getAllElements()) item.removeView(model);
			model.removeAllItems();
			model.updateAfterRemove();
		}
	};
	
	public SListView<T> getListView() { return list_view; }
}
