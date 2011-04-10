package satori.thrift;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import satori.common.SException;
import satori.problem.SProblemReader;
import satori.session.SSession;
import satori.thrift.gen.Problem;
import satori.thrift.gen.ProblemStruct;

public class SProblemData {
	static class ProblemWrap implements SProblemReader {
		private ProblemStruct struct;
		public ProblemWrap(ProblemStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	
	private static class LoadCommand implements SThriftCommand {
		private final long id;
		private SProblemReader result;
		public SProblemReader getResult() { return result; }
		public LoadCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Problem.Iface iface = new Problem.Client(SThriftClient.getProtocol());
			result = new ProblemWrap(iface.Problem_get_struct(SSession.getToken(), id));
		}
	}
	public static SProblemReader load(long id) throws SException {
		LoadCommand command = new LoadCommand(id);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static ProblemStruct createStruct(SProblemReader problem) {
		ProblemStruct struct = new ProblemStruct();
		struct.setName(problem.getName());
		struct.setDescription(problem.getDescription());
		return struct;
	}
	
	private static class CreateCommand implements SThriftCommand {
		private final SProblemReader problem;
		private long result;
		public long getResult() { return result; }
		public CreateCommand(SProblemReader problem) { this.problem = problem; }
		@Override public void call() throws Exception {
			Problem.Iface iface = new Problem.Client(SThriftClient.getProtocol());
			result = iface.Problem_create(SSession.getToken(), createStruct(problem)).getId();
		}
	}
	public static long create(SProblemReader problem) throws SException {
		CreateCommand command = new CreateCommand(problem);
		SThriftClient.call(command);
		return command.getResult();
	}
	
	private static class SaveCommand implements SThriftCommand {
		private final SProblemReader problem;
		public SaveCommand(SProblemReader problem) { this.problem = problem; }
		@Override public void call() throws Exception {
			Problem.Iface iface = new Problem.Client(SThriftClient.getProtocol());
			iface.Problem_modify(SSession.getToken(), problem.getId(), createStruct(problem));
		}
	}
	public static void save(SProblemReader problem) throws SException {
		SThriftClient.call(new SaveCommand(problem));
	}
	
	private static class DeleteCommand implements SThriftCommand {
		private final long id;
		public DeleteCommand(long id) { this.id = id; }
		@Override public void call() throws Exception {
			Problem.Iface iface = new Problem.Client(SThriftClient.getProtocol());
			iface.Problem_delete(SSession.getToken(), id);
		}
	}
	public static void delete(long id) throws SException {
		SThriftClient.call(new DeleteCommand(id));
	}
	
	private static class ListCommand implements SThriftCommand {
		private List<SProblemReader> result;
		public List<SProblemReader> getResult() { return result; }
		@Override public void call() throws Exception {
			Problem.Iface iface = new Problem.Client(SThriftClient.getProtocol());
			ProblemStruct filter = new ProblemStruct();
			List<ProblemStruct> list = iface.Problem_filter(SSession.getToken(), filter);
			result = new ArrayList<SProblemReader>();
			for (ProblemStruct struct : list) result.add(new ProblemWrap(struct));
		}
	}
	public static List<SProblemReader> list() throws SException {
		ListCommand command = new ListCommand();
		SThriftClient.call(command);
		return Collections.unmodifiableList(command.getResult());
	}
}
