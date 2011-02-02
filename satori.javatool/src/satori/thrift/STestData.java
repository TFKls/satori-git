package satori.thrift;

import static satori.thrift.SAttributeData.createAttrMap;
import static satori.thrift.SAttributeData.createBlobs;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttributeReader;
import satori.common.SAssert;
import satori.common.SException;
import satori.session.SSession;
import satori.test.STestBasicReader;
import satori.test.STestReader;
import satori.thrift.SAttributeData.AttributeWrap;
import satori.thrift.gen.Test;
import satori.thrift.gen.TestStruct;

public class STestData {
	static class TestBasicWrap implements STestBasicReader {
		private TestStruct struct;
		public TestBasicWrap(TestStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public long getProblemId() { return struct.getProblem(); }
		@Override public String getName() { return struct.getName(); }
	}
	static class TestWrap extends TestBasicWrap implements STestReader {
		private SAttributeReader data;
		public TestWrap(TestStruct struct) { super(struct); }
		public void setData(SAttributeReader data) { this.data = data; }
		@Override public SAttributeReader getData() { return data; }
	}
	
	static Iterable<STestBasicReader> createTestList(Iterable<TestStruct> structs) {
		List<STestBasicReader> tests = new ArrayList<STestBasicReader>();
		for (TestStruct struct : structs) tests.add(new TestBasicWrap(struct));
		return tests;
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TestWrap result;
		public STestReader getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			result = new TestWrap(iface.Test_get_struct(SSession.getToken(), id));
			result.setData(new AttributeWrap(iface.Test_data_get_map(SSession.getToken(), id)));
		}
	}
	public static STestReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static TestStruct createStruct(STestBasicReader test) {
		TestStruct struct = new TestStruct();
		struct.setProblem(test.getProblemId());
		struct.setName(test.getName());
		return struct;
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final STestReader test;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(STestReader test) { this.test = test; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			result = iface.Test_create(SSession.getToken(), createStruct(test), createAttrMap(test.getData())).getId();
		}
	}
	public static long create(STestReader test) throws SException {
		SAssert.assertNotNull(test.getData(), "Attribute map is null");
		createBlobs(test.getData());
		CreateCommand command = new CreateCommand(test);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SaveCommand implements SThriftCommand {
		private final STestReader test;
		public SaveCommand(STestReader test) { this.test = test; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			iface.Test_modify_full(SSession.getToken(), test.getId(), createStruct(test), createAttrMap(test.getData()));
		}
	}
	public static void save(STestReader test) throws SException {
		SAssert.assertNotNull(test.getData(), "Attribute map is null");
		createBlobs(test.getData());
		SThriftClient.call(new SaveCommand(test));
	}
	
	private static class DeleteCommand implements SThriftCommand {
		private final long id;
		public DeleteCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			iface.Entity_delete(SSession.getToken(), id);
		}
	}
	public static void delete(long id) throws SException {
		SThriftClient.call(new DeleteCommand(id));
	}
	
	private static class ListCommand implements SThriftCommand {
		private final long problem_id;
		private List<STestBasicReader> result;
		public ListCommand(long problem_id) { this.problem_id = problem_id; }
		public Iterable<STestBasicReader> getResult() { return result; }
		@Override public void call() throws Exception {
			Test.Iface iface = new Test.Client(SThriftClient.getProtocol());
			TestStruct filter = new TestStruct();
			filter.setProblem(problem_id);
			List<TestStruct> list = iface.Test_filter(SSession.getToken(), filter);
			result = new ArrayList<STestBasicReader>();
			for (TestStruct struct : list) result.add(new TestBasicWrap(struct));
		}
	}
	public static Iterable<STestBasicReader> list(long problem_id) throws SException {
		ListCommand command = new ListCommand(problem_id);
		SThriftClient.call(command);
		return command.getResult();
	}
}
