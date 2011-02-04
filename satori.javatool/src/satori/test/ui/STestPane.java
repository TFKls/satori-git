package satori.test.ui;

import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Graphics;
import java.awt.Insets;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.dnd.DropTargetDragEvent;
import java.awt.dnd.DropTargetDropEvent;
import java.awt.dnd.DropTargetEvent;
import java.awt.dnd.DropTargetListener;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.TooManyListenersException;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.TransferHandler;

import satori.common.SException;
import satori.common.SList;
import satori.common.SListener0;
import satori.common.SListener1;
import satori.common.SListener2;
import satori.common.ui.SPane;
import satori.common.ui.SScrollPane;
import satori.main.SFrame;
import satori.problem.impl.STestSuiteImpl;
import satori.test.STestSnap;
import satori.test.impl.SSolution;
import satori.test.impl.STestFactory;
import satori.test.impl.STestImpl;

public class STestPane implements SList<STestImpl>, SPane {
	private final STestSuiteImpl suite;
	private final STestFactory factory;
	
	private STestInputPane input_pane;
	private List<SSolutionPane> solution_panes = new ArrayList<SSolutionPane>();
	private List<STestImpl> tests = new ArrayList<STestImpl>();
	
	private JComponent pane;
	private SScrollPane scroll_pane;
	
	private SListener0 new_test_listener = new SListener0() {
		@Override public void call() {
			STestImpl test = factory.createNew();
			suite.addTest(test);
			add(test);
		}
	};
	private SListener1<STestImpl> close_test_listener = new SListener1<STestImpl>() {
		@Override public void call(STestImpl test) {
			remove(test);
			suite.removeTest(test);
		}
	};
	private SListener1<SSolutionPane> remove_solution_listener = new SListener1<SSolutionPane>() {
		@Override public void call(SSolutionPane removed_pane) { removeSolutionPane(removed_pane); }
	};
	
	private int indicator_index = -1;
	private Rectangle indicator_rect = null;
	private boolean accept_drop = false;
	
	private int getDropIndex(Point location) {
		int index = (int)Math.round((location.getX() - SDimension.labelWidth) / SDimension.itemWidth);
		if (index < 0) index = 0;
		if (index > tests.size()) index = tests.size();
		return index;
	}
	private void indicateDrop(Point location) {
		int index = location != null && accept_drop ? getDropIndex(location) : -1;
		if (index == indicator_index) return;
		indicator_index = index;
		if (indicator_rect != null) {
			input_pane.getPane().repaint(indicator_rect);
			indicator_rect = null;
		}
		if (index == -1) return;
		int x = SDimension.labelWidth + index * SDimension.itemWidth - 1;
		int height = input_pane.getPane().getHeight();
		indicator_rect = new Rectangle(x, 0, 1, height);
		input_pane.getPane().repaint(indicator_rect);
	}
	
	private static class MoveTestTransferable implements Transferable {
		private final STestTransfer data;
		public MoveTestTransferable(STestTransfer data) { this.data = data; }
		@Override public DataFlavor[] getTransferDataFlavors() {
			DataFlavor[] flavors = new DataFlavor[1];
			flavors[0] = STestTransfer.flavor;
			return flavors;
		}
		@Override public boolean isDataFlavorSupported(DataFlavor flavor) {
			return flavor.match(STestTransfer.flavor);
		}
		@Override public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
			if (flavor.match(STestTransfer.flavor)) return data;
			else throw new UnsupportedFlavorException(flavor);
		}
	}
	@SuppressWarnings("serial")
	private class TestTransferHandler extends TransferHandler implements SListener2<STestImpl, MouseEvent> {
		private STestImpl test;
		
		@Override public boolean canImport(TransferSupport support) {
			if (!support.isDrop()) return false;
			accept_drop = false;
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) {
				if ((support.getSourceDropActions() & COPY) != COPY) return false;
				support.setDropAction(COPY);
				accept_drop = true;
				return true;
			}
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				if ((support.getSourceDropActions() & MOVE) != MOVE) return false;
				support.setDropAction(MOVE);
				Transferable t = support.getTransferable();
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				accept_drop = true;
				return true;
			}
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			accept_drop = false;
			Transferable t = support.getTransferable();
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) {
				STestSnapTransfer data;
				try { data = (STestSnapTransfer)t.getTransferData(STestSnapTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				List<STestImpl> new_tests = new ArrayList<STestImpl>();
				for (STestSnap snap : data.get()) {
					if (suite.hasTest(snap.getId())) continue;
					try { new_tests.add(factory.create(snap)); }
					catch(SException ex) { SFrame.showErrorDialog(ex); return false; }
				}
				int index = getDropIndex(support.getDropLocation().getDropPoint());
				int cur_index = index;
				for (STestImpl test : new_tests) suite.addTest(test, cur_index++);
				add(new_tests, index);
				return true;
			}
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				STestImpl test = data.getTest();
				int index = getDropIndex(support.getDropLocation().getDropPoint());
				suite.moveTest(test, index);
				move(test, index);
				return true;
			}
			return false;
		}
		@Override protected Transferable createTransferable(JComponent c) {
			return new MoveTestTransferable(new STestTransfer(test, suite));
		}
		@Override public int getSourceActions(JComponent c) { return MOVE; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
		@Override public void call(STestImpl test, MouseEvent e) {
			this.test = test;
			exportAsDrag(scroll_pane.getPane(), e, TransferHandler.MOVE);
		}
	}
	private TestTransferHandler transfer_handler = new TestTransferHandler();
	
	private DropTargetListener drop_listener = new DropTargetListener() {
		@Override public void dragEnter(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
		@Override public void dragOver(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
		@Override public void dragExit(DropTargetEvent e) { indicateDrop(null); }
		@Override public void drop(DropTargetDropEvent e) { indicateDrop(null); }
		@Override public void dropActionChanged(DropTargetDragEvent e) { indicateDrop(e.getLocation()); }
	};
	
	public STestPane(STestSuiteImpl suite, STestFactory factory) {
		this.suite = suite;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return scroll_pane.getPane(); }
	
	@SuppressWarnings("serial")
	private class Pane extends Box {
		public Pane() { super(BoxLayout.Y_AXIS); }
		@Override public void paint(Graphics g) {
			super.paint(g);
			if (indicator_rect == null) return;
			g.setColor(Color.BLUE);
			g.fillRect(indicator_rect.x, indicator_rect.y, indicator_rect.width, indicator_rect.height);
		}
	}
	
	private void initialize() {
		pane = new Pane();
		input_pane = new STestInputPane();
		input_pane.addRow(new SStatusRowView());
		input_pane.addRow(new SButtonRowView(transfer_handler, close_test_listener, new_test_listener));
		input_pane.addRow(new SInfoRowView());
		input_pane.addRow(new SDataRowView());
		pane.add(input_pane.getPane());
		JPanel bottom_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JButton bottom_button = new JButton("Add solution");
		bottom_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonHeight(bottom_button);
		bottom_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { addSolutionPane(); }
		});
		bottom_pane.add(bottom_button);
		pane.add(bottom_pane);
		scroll_pane = new SScrollPane();
		scroll_pane.setView(pane);
		scroll_pane.getPane().setTransferHandler(transfer_handler);
		try { scroll_pane.getPane().getDropTarget().addDropTargetListener(drop_listener); }
		catch(TooManyListenersException ex) {}
	}
	
	private void addSolutionPane() {
		SSolution solution = new SSolution();
		SSolutionPane new_pane = new SSolutionPane(solution, remove_solution_listener);
		pane.add(new_pane.getPane(), solution_panes.size()+1);
		solution_panes.add(new_pane);
		int index = 0;
		for (STestImpl test : tests) new_pane.addColumn(test, index++);
		pane.revalidate(); pane.repaint();
	}
	private void removeSolutionPane(SSolutionPane removed_pane) {
		for (int index = tests.size()-1; index >= 0; --index) removed_pane.removeColumn(index);
		pane.remove(solution_panes.indexOf(removed_pane)+1);
		solution_panes.remove(removed_pane);
		pane.revalidate(); pane.repaint();
	}
	
	private void addColumn(STestImpl test, int index) {
		input_pane.addColumn(test, index);
		for (SRowView pane : solution_panes) pane.addColumn(test, index);
	}
	private void removeColumn(int index) {
		input_pane.removeColumn(index);
		for (SRowView pane : solution_panes) pane.removeColumn(index);
	}
	
	@Override public void add(STestImpl test) {
		int index = tests.size();
		tests.add(test);
		addColumn(test, index);
		pane.revalidate(); pane.repaint();
	}
	public void add(Iterable<STestImpl> tests, int index) {
		for (STestImpl test : tests) {
			this.tests.add(index, test);
			addColumn(test, index++);
		}
		pane.revalidate(); pane.repaint();
	}
	@Override public void add(Iterable<STestImpl> tests) {
		add(tests, this.tests.size());
	}
	@Override public void remove(STestImpl test) {
		removeColumn(tests.indexOf(test));
		tests.remove(test);
		pane.revalidate(); pane.repaint();
	}
	@Override public void removeAll() {
		for (int i = tests.size()-1; i >= 0; --i) removeColumn(i);
		tests.clear();
		pane.revalidate(); pane.repaint();
	}
	public void move(STestImpl test, int index) {
		int old_index = tests.indexOf(test);
		removeColumn(old_index);
		tests.remove(test);
		if (old_index < index) --index;
		tests.add(index, test);
		addColumn(test, index);
		pane.revalidate(); pane.repaint();
	}
}
