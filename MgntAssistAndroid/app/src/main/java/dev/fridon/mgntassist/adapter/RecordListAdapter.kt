package dev.fridon.mgntassist.adapter

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import dev.fridon.mgntassist.data.Record
import dev.fridon.mgntassist.databinding.ItemRecordBinding
import dev.fridon.mgntassist.list.RecyclerViewOnClickListener

class RecordListAdapter constructor(
    private val listener: RecyclerViewOnClickListener
) : ListAdapter<Record, RecordItemHolder>(DiffCallBack()) {

    override fun onCreateViewHolder(
        parent: ViewGroup,
        viewType: Int
    ): RecordItemHolder {
        val binding = ItemRecordBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return RecordItemHolder(binding)
    }

    override fun onBindViewHolder(
        holder: RecordItemHolder,
        position: Int
    ) {
        val item = getItem(position)
        holder.itemRecordBinding.parentCard.setOnClickListener {
            listener.onItemClick(position)
        }
        holder.bind(item)
    }
}

class DiffCallBack : DiffUtil.ItemCallback<Record>() {
    override fun areItemsTheSame(
        oldItem: Record,
        newItem: Record
    ) = oldItem.title == newItem.title

    override fun areContentsTheSame(
        oldItem: Record,
        newItem: Record
    ) =
        oldItem == newItem
}

class RecordItemHolder constructor(
    val itemRecordBinding: ItemRecordBinding,
) : RecyclerView.ViewHolder(itemRecordBinding.root) {

    fun bind(record: Record) {
        itemRecordBinding.recordTitle.text = record.title
    }
}
