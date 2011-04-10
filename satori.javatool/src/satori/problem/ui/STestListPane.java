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
import java.util.Comparator;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;
import javax.swing.TransferHandler;

import satori.common.SListener0;
import satori.common.SListener1;
import satori.common.ui.SListPane;
import satori.common.ui.SPane;
import satori.problem.STestList;
import satori.test.STestSnap;
import satori.test.ui.STestSnapTransfer;

public class STestListPane implements SPane, SListener1<STestList> {
	private final SListener0 new_listener;
	private final SListener1<List<STestSnap>> open_listener;
	
	private STestList test_list = null;
	
	private final JButton new_button, open_button;
	private final SListPane<STestSnap> list;
	private final JComponent pane;
	
	public STestListPane(SListener0 new_listener, SListener1<List<STestSnap>> open_listener) {
		this.new_listener = new_listener;
		this.open_listener = open_listener;
		new_button = new JButton("New");
		new_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { newRequest(); }
		});
		open_button = new JButton("Open");
		open_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { openRequest(); }
		});
		JComponent button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		button_pane.add(new_button);
		button_pane.add(open_button);
		list = new SListPane<STestSnap>(new Comparator<STestSnap>() {
			@Override public int compare(STestSnap t1, STestSnap t2) {
				return t1.getName().compareTo(t2.getName());
			}
		}, true);
		list.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
		list.addColumn(new SListPane.Column<STestSnap>() {
			@Override public String get(STestSnap test) {
				String name = test.getName();
				return name.isEmpty() ? "(Test)" : name;
			}
		}, 1.0f);
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
		pane = new JPanel(new BorderLayout());
		pane.add(button_pane, BorderLayout.NORTH);
		pane.add(new JScrollPane(list), BorderLayout.CENTER);
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void newRequest() { new_listener.call(); }
	private void openRequest() {
		if (list.isSelectionEmpty()) return;
		List<STestSnap> snaps = new ArrayList<STestSnap>();
		for (int index : list.getSelectedIndices()) snaps.add(list.getItem(index));
		open_listener.call(snaps);
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
			for (int index : list.getSelectedIndices()) tests.add(list.getItem(index));
			return new TestTransferable(tests);
		}
		@Override public int getSourceActions(JComponent c) { return COPY; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
	}
	
	@Override public void call(STestList test_list) {
		if (this.test_list != null) this.test_list.removePane(list.getListView());
		this.test_list = test_list;
		if (this.test_list != null) this.test_list.addPane(list.getListView());
	}
}
