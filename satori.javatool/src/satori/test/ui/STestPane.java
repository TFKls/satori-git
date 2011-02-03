package satori.test.ui;

import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.Point;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.TransferHandler;

import satori.common.SException;
import satori.common.SList;
import satori.common.SListener;
import satori.common.SListener2;
import satori.common.ui.SPane;
import satori.common.ui.SScrollPane;
import satori.main.SFrame;
import satori.problem.impl.STestSuiteImpl;
import satori.test.STestSnap;
import satori.test.impl.SSolution;
import satori.test.impl.STestFactory;
import satori.test.impl.STestImpl;
import satori.test.meta.STestMetadata;

public class STestPane implements SList<STestImpl>, SPane {
	private final STestMetadata meta;
	private final STestSuiteImpl suite;
	private final STestFactory factory;
	
	private STestInputPane input_pane;
	private List<SSolutionPane> solution_panes = new ArrayList<SSolutionPane>();
	private List<STestImpl> tests = new ArrayList<STestImpl>();
	
	private JComponent pane;
	private SScrollPane scroll_pane;
	
	private SListener<STestImpl> new_test_listener = new SListener<STestImpl>() {
		@Override public void call(STestImpl unused) {
			STestImpl test = factory.createNew();
			suite.addTest(test);
			add(test);
		}
	};
	private SListener<STestImpl> close_test_listener = new SListener<STestImpl>() {
		@Override public void call(STestImpl test) {
			remove(test);
			suite.removeTest(test);
		}
	};
	private SListener<SSolutionPane> remove_solution_listener = new SListener<SSolutionPane>() {
		@Override public void call(SSolutionPane removed_pane) { removeSolutionPane(removed_pane); }
	};
	
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
			if ((support.getSourceDropActions() & COPY) != COPY) return false;
			support.setDropAction(COPY);
			if (support.isDataFlavorSupported(STestSnapTransfer.flavor)) return true;
			if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				Transferable t = support.getTransferable();
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				return data.getTestSuite() == suite;
			}
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
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
				Point pos = support.getDropLocation().getDropPoint();
				int index = (int)Math.round((pos.getX()-120)/120);
				if (index < 0) index = 0;
				if (index > tests.size()) index = tests.size();
				int cur_index = index;
				for (STestImpl test : new_tests) suite.addTest(test, cur_index++);
				add(new_tests, index);
				return true;
			}
			else if (support.isDataFlavorSupported(STestTransfer.flavor)) {
				STestTransfer data;
				try { data = (STestTransfer)t.getTransferData(STestTransfer.flavor); }
				catch(UnsupportedFlavorException ex) { return false; }
				catch(IOException ex) { return false; }
				if (data.getTestSuite() != suite) return false;
				STestImpl test = data.getTest();
				Point pos = support.getDropLocation().getDropPoint();
				int index = (int)Math.round((pos.getX()-120)/120);
				if (index < 0) index = 0;
				if (index > tests.size()) index = tests.size();
				suite.moveTest(test, index);
				move(test, index);
				return true;
			}
			else return false;
		}
		@Override protected Transferable createTransferable(JComponent c) {
			return new MoveTestTransferable(new STestTransfer(test, suite));
		}
		@Override public int getSourceActions(JComponent c) { return COPY; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
		@Override public void call(STestImpl test, MouseEvent e) {
			this.test = test;
			exportAsDrag(scroll_pane.getPane(), e, TransferHandler.COPY);
		}
	}
	private TestTransferHandler transfer_handler = new TestTransferHandler();
	
	public STestPane(STestMetadata meta, STestSuiteImpl suite, STestFactory factory) {
		this.meta = meta;
		this.suite = suite;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return scroll_pane.getPane(); }
	
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		input_pane = new STestInputPane();
		input_pane.addRow(new SGenericRowView("Status", new SStatusItemView.Factory()));
		input_pane.addRow(new SButtonRowView(new SButtonItemView.Factory(transfer_handler, close_test_listener), new_test_listener));
		input_pane.addRow(new SGenericRowView("Name", new SInfoItemView.Factory()));
		input_pane.addRow(new SDataRowView(meta));
		pane.add(input_pane.getPane());
		JPanel bottom_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JButton bottom_button = new JButton("Add solution");
		bottom_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setHeight(bottom_button);
		bottom_button.setFocusable(false);
		bottom_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { addSolutionPane(); }
		});
		bottom_pane.add(bottom_button);
		pane.add(bottom_pane);
		
		scroll_pane = new SScrollPane();
		scroll_pane.setView(pane);
		scroll_pane.getPane().setTransferHandler(transfer_handler);
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
