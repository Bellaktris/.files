local utils = require "mp.utils"

del_list = {}

function contains_item(l, i)
   for k, v in pairs(l) do
      if v == i then
         mp.osd_message("unremoving current file")
         l[k] = nil
         return true
      end
   end
   mp.osd_message("removing current file")
   return false
end

function mark_delete()
   local work_dir = mp.get_property_native("working-directory")
   local file_path = mp.get_property_native("path")
   local s = file_path:find(work_dir, 0, true)
   local final_path
   if s and s == 0 then
      final_path = file_path
   else
      final_path = utils.join_path(work_dir, file_path)
   end
   if not contains_item(del_list, final_path) then
      table.insert(del_list, final_path)
   end
end

mp.add_key_binding("ctrl+d", "file-utils", mark_delete)

function delete()
   for i, v in pairs(del_list) do
      print("deleting: " .. v)
      os.remove(v)
   end
end

mp.register_event("shutdown", delete)

move_to_dir = os.getenv('MOVE_TO_DIR')

if move_to_dir ~= nil then
   -- if lfs.attributes(move_to_dir, 'mode') ~= nil then
      move_list = {}

      function splitpath(P)
          local i = #P
          ch = P:sub(i, i)
          while i > 0 and ch ~= "/" do
              i = i - 1
              ch = P:sub(i, i)
          end
          if i == 0 then
              return '', P
          else
              return P:sub(1, i - 1), P:sub(i + 1)
          end
      end

      function mark_move()
         local work_dir = mp.get_property_native("working-directory")
         local file_path = mp.get_property_native("path")
         local s = file_path:find(work_dir, 0, true)
         local final_path
         if s and s == 0 then
            final_path = file_path
         else
            final_path = utils.join_path(work_dir, file_path)
         end
         if not contains_item(move_list, final_path) then
            table.insert(move_list, final_path)
         end
      end

      mp.add_key_binding("ctrl+m", "file-utils", mark_move)

      function move()
         for i, v in pairs(move_list) do
            local _, vbase = splitpath(v)
            print("moving: " .. v .. " to " .. move_to_dir .. "/" .. vbase)
            os.rename(v, move_to_dir .. "/" .. vbase)
         end
      end

      mp.register_event("shutdown", move)
   -- end
end
