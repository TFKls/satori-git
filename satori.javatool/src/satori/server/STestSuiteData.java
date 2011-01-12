package satori.server;

import static satori.server.STestData.createTestList;

import java.util.ArrayList;
import java.util.List;

import satori.common.SException;
import satori.login.SLogin;
import satori.problem.STestSuiteBasicReader;
import satori.problem.STestSuiteReader;
import satori.test.STestBasicReader;
import satori.thrift.SThriftClient;
import satori.thrift.SThriftCommand;
import satori.thrift.gen.TestSuite;
import satori.thrift.gen.TestSuiteStruct;

public class STestSuiteData {
	static class TestSuiteBasicWrap implements STestSuiteBasicReader {
		private TestSuiteStruct struct;
		public TestSuiteBasicWrap(TestSuiteStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public long getProblemId() { return struct.getProblem(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	static class TestSuiteWrap extends TestSuiteBasicWrap implements STestSuiteReader {
		private Iterable<STestBasicReader> tests;
		public TestSuiteWrap(TestSuiteStruct struct) { super(struct); }
		public void setTests(Iterable<STestBasicReader> tests) { this.tests = tests; }
		@Override public Iterable<STestBasicReader> getTests() { return tests; }
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private TestSuiteWrap result;
		public STestSuiteReader getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			result = new TestSuiteWrap(iface.TestSuite_get_struct(SLogin.getToken(), id));
			result.setTests(createTestList(iface.TestSuite_get_tests(SLogin.getToken(), id)));
			//TODO: load tests
		}
	}
	public static STestSuiteReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static TestSuiteStruct createStruct(STestSuiteBasicReader suite) {
		TestSuiteStruct struct = new TestSuiteStruct();
		struct.setProblem(suite.getProblemId());
		struct.setName(suite.getName());
		struct.setDescription(suite.getDescription());
		struct.setDispatcher("SerialDispatcher");
		struct.setAccumulators("StatusAccumulator");
		return struct;
	}
	private static List<Long> createTestIdList(Iterable<? extends STestBasicReader> tests) {
		List<Long> list = new ArrayList<Long>();
		for (STestBasicReader test : tests) list.add(test.getId());
		return list;
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final STestSuiteReader suite;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(STestSuiteReader suite) { this.suite = suite; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			result = iface.TestSuite_create(SLogin.getToken(), createStruct(suite), createTestIdList(suite.getTests())).getId();
		}
	}
	public static long create(STestSuiteReader suite) throws SException {
		if (suite.getTests() == null) throw new RuntimeException("List of tests is null");
		CreateCommand command = new CreateCommand(suite);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SaveCommand implements SThriftCommand {
		private final STestSuiteReader suite;
		public SaveCommand(STestSuiteReader suite) { this.suite = suite; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			iface.TestSuite_modify_full(SLogin.getToken(), suite.getId(), createStruct(suite), createTestIdList(suite.getTests()));
		}
	}
	public static void save(STestSuiteReader suite) throws SException {
		if (suite.getTests() == null) throw new RuntimeException("List of tests is null");
		SThriftClient.call(new SaveCommand(suite));
	}
	
	private static class DeleteCommand implements SThriftCommand {
		private final long id;
		public DeleteCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			iface.TestSuite_delete(SLogin.getToken(), id);
		}
	}
	public static void delete(long id) throws SException {
		SThriftClient.call(new DeleteCommand(id));
	}
	
	private static class ListCommand implements SThriftCommand {
		private final long problem_id;
		private List<STestSuiteBasicReader> result;
		public ListCommand(long problem_id) { this.problem_id = problem_id; }
		public Iterable<STestSuiteBasicReader> getResult() { return result; }
		@Override public void call() throws Exception {
			TestSuite.Iface iface = new TestSuite.Client(SThriftClient.getProtocol());
			TestSuiteStruct filter = new TestSuiteStruct();
			filter.setProblem(problem_id);
			List<TestSuiteStruct> list = iface.TestSuite_filter(SLogin.getToken(), filter);
			result = new ArrayList<STestSuiteBasicReader>();
			for (TestSuiteStruct struct : list) result.add(new TestSuiteBasicWrap(struct));
		}
	}
	public static Iterable<STestSuiteBasicReader> list(long problem_id) throws SException {
		ListCommand command = new ListCommand(problem_id);
		SThriftClient.call(command);
		return command.getResult();
	}
}
