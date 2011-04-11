package satori.data;

import java.util.AbstractList;
import java.util.List;

import satori.problem.SProblemReader;
import satori.session.SSession;
import satori.task.STaskManager;
import satori.thrift.gen.Problem;
import satori.thrift.gen.ProblemStruct;

public class SProblemData {
	static class ProblemWrap implements SProblemReader {
		private final ProblemStruct struct;
		public ProblemWrap(ProblemStruct struct) { this.struct = struct; }
		@Override public boolean hasId() { return true; }
		@Override public long getId() { return struct.getId(); }
		@Override public String getName() { return struct.getName(); }
		@Override public String getDescription() { return struct.getDescription(); }
	}
	static class ProblemListWrap extends AbstractList<SProblemReader> {
		private final List<ProblemStruct> list;
		public ProblemListWrap(List<ProblemStruct> list) { this.list = list; }
		@Override public int size() { return list.size(); }
		@Override public SProblemReader get(int index) { return new ProblemWrap(list.get(index)); }
	}
	
	public static SProblemReader load(long id) throws Exception {
		STaskManager.log("Loading problem...");
		Problem.Iface iface = new Problem.Client(SSession.getProtocol());
		return new ProblemWrap(iface.Problem_get_struct(SSession.getToken(), id));
	}
	
	private static ProblemStruct createStruct(SProblemReader problem) {
		ProblemStruct struct = new ProblemStruct();
		struct.setName(problem.getName());
		struct.setDescription(problem.getDescription());
		return struct;
	}
	
	public static long create(SProblemReader problem) throws Exception {
		STaskManager.log("Creating problem...");
		Problem.Iface iface = new Problem.Client(SSession.getProtocol());
		return iface.Problem_create(SSession.getToken(), createStruct(problem)).getId();
	}
	public static void save(SProblemReader problem) throws Exception {
		STaskManager.log("Saving problem...");
		Problem.Iface iface = new Problem.Client(SSession.getProtocol());
		iface.Problem_modify(SSession.getToken(), problem.getId(), createStruct(problem));
	}
	public static void delete(long id) throws Exception {
		STaskManager.log("Deleting problem...");
		Problem.Iface iface = new Problem.Client(SSession.getProtocol());
		iface.Problem_delete(SSession.getToken(), id);
	}
	public static List<SProblemReader> list() throws Exception {
		STaskManager.log("Loading problem list...");
		Problem.Iface iface = new Problem.Client(SSession.getProtocol());
		ProblemStruct filter = new ProblemStruct();
		return new ProblemListWrap(iface.Problem_filter(SSession.getToken(), filter));
	}
}
