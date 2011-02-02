package satori.problem.ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

import javax.swing.AbstractListModel;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;
import javax.swing.TransferHandler;

import satori.common.SList;
import satori.common.SView;
import satori.common.ui.SPane;
import satori.test.STestSnap;

public class STestListPane implements SList<STestSnap>, SPane {
	private final SProblemPane parent;
	
	@SuppressWarnings("serial")
	private static class ListModel extends AbstractListModel implements SView {
		private List<STestSnap> list = new ArrayList<STestSnap>();
		private Comparator<STestSnap> comparator = new Comparator<STestSnap>() {
			@Override public int compare(STestSnap t1, STestSnap t2) {
				return t1.getName().compareTo(t2.getName());
			}
		};
		
		public STestSnap getItem(int index) { return list.get(index); }
		public Iterable<STestSnap> getItems() { return list; }
		
		public void addItem(STestSnap test) { list.add(test); }
		public void removeItem(STestSnap test) { list.remove(test); }
		public void removeAllItems() { list.clear(); }
		
		@Override public void update() {
			Collections.sort(list, comparator);
			fireContentsChanged(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterAdd() {
			Collections.sort(list, comparator);
			fireIntervalAdded(this, 0, list.isEmpty() ? 0 : list.size()-1);
		}
		public void updateAfterRemove() { fireIntervalRemoved(this, 0, list.isEmpty() ? 0 : list.size()-1); }
		
		@Override public String getElementAt(int index) {
			String name = list.get(index).getName();
			return name.isEmpty() ? "(Test)" : name;
		}
		@Override public int getSize() { return list.size(); }
	}
	
	private ListModel list_model = new ListModel();
	
	private JPanel main_pane;
	private JPanel button_pane;
	private JButton new_button, open_button;
	private JList list;
	private JScrollPane list_pane;
	
	public STestListPane(SProblemPane parent) {
		this.parent = parent;
		initialize();
	}
	
	@Override public JComponent getPane() { return main_pane; }
	
	private void newRequest() { parent.newTest(); }
	private void openRequest() {
		if (list.isSelectionEmpty()) return;
		Collection<STestSnap> snaps = new ArrayList<STestSnap>();
		for (int index : list.getSelectedIndices()) snaps.add(list_model.getItem(index));
		parent.openTests(snaps);
	}
	
	private static class TestTransferable implements Transferable {
		private final STestSnapTransfer data;
		public TestTransferable(STestSnapTransfer data) { this.data = data; }
		@Override public DataFlavor[] getTransferDataFlavors() {
			DataFlavor[] flavors = new DataFlavor[1];
			flavors[0] = STestSnapTransfer.flavor;
			return flavors;
		}
		@Override public boolean isDataFlavorSupported(DataFlavor flavor) {
			return flavor.match(STestSnapTransfer.flavor);
		}
		@Override public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
			if (flavor.match(STestSnapTransfer.flavor)) return data;
			else throw new UnsupportedFlavorException(flavor);
		}
	}
	@SuppressWarnings("serial")
	private class TestTransferHandler extends TransferHandler {
		@Override public boolean canImport(TransferSupport support) { return false; }
		@Override public boolean importData(TransferSupport support) { return false; }
		@Override protected Transferable createTransferable(JComponent c) {
			STestSnapTransfer tests = new STestSnapTransfer();
			for (int index : list.getSelectedIndices()) tests.add(list_model.getItem(index));
			return new TestTransferable(tests);
		}
		@Override public int getSourceActions(JComponent c) { return COPY; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
	}
	
	private void initialize() {
		main_pane = new JPanel();
		main_pane.setLayout(new BorderLayout());
		button_pane = new JPanel();
		button_pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		new_button = new JButton("New");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		button_pane.add(new_button);
		open_button = new JButton("Open");
		open_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { openRequest(); }
		});
		button_pane.add(open_button);
		main_pane.add(button_pane, BorderLayout.NORTH);
		list = new JList(list_model);
		list.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
		MouseAdapter mouse_listener = new MouseAdapter() {
			@Override public void mouseClicked(MouseEvent e) {
				if (e.getClickCount() == 2) { e.consume(); openRequest(); }
			}
			@Override public void mouseDragged(MouseEvent e) {
				if (list.isSelectionEmpty()) return;
				list.getTransferHandler().exportAsDrag(list, e, TransferHandler.COPY);
			}
		};
		list.addMouseListener(mouse_listener);
		list.addMouseMotionListener(mouse_listener);
		list.setTransferHandler(new TestTransferHandler());
		list_pane = new JScrollPane(list);
		main_pane.add(list_pane, BorderLayout.CENTER);
	}
	
	@Override public void add(STestSnap test) {
		list.clearSelection();
		list_model.addItem(test);
		test.addView(list_model);
		list_model.updateAfterAdd();
	}
	@Override public void add(Iterable<STestSnap> tests) {
		list.clearSelection();
		for (STestSnap t : tests) {
			list_model.addItem(t);
			t.addView(list_model);
		}
		list_model.updateAfterAdd();
	}
	@Override public void remove(STestSnap test) {
		list.clearSelection();
		test.removeView(list_model);
		list_model.removeItem(test);
		list_model.updateAfterRemove();
	}
	@Override public void removeAll() {
		list.clearSelection();
		for (STestSnap t : list_model.getItems()) t.removeView(list_model);
		list_model.removeAllItems();
		list_model.updateAfterRemove();
	}
}
